"""Online public-data ingestion for INSPECT-AI.

This module deliberately separates public context from confirmed inspection
outcomes. External sources can enrich operational monitoring and training
features, but they never create a supervised risk label.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

import httpx
from sqlalchemy.orm import Session

from services.api.app.models import ExternalDataObservationDB

DATAGOV_BASE_URL = "https://api.data.gov.in/resource"
IMD_BASE_URL = "https://mausam.imd.gov.in/api"
HTTP_TIMEOUT = float(os.getenv("ONLINE_DATA_HTTP_TIMEOUT", "20"))


SOURCE_CATALOG = {
    "imd_current_weather": {
        "source": "IMD",
        "dataset": "Current Weather",
        "mode": "realtime",
        "endpoint": f"{IMD_BASE_URL}/current_wx_api.php",
        "auth_env": "IMD_API_TOKEN",
        "description": "Current weather observations.",
    },
    "imd_district_rainfall": {
        "source": "IMD",
        "dataset": "District Rainfall",
        "mode": "realtime",
        "endpoint": f"{IMD_BASE_URL}/districtwise_rainfall_api.php",
        "auth_env": "IMD_API_TOKEN",
        "description": "District-wise rainfall observations.",
    },
    "imd_district_warning": {
        "source": "IMD",
        "dataset": "District Warning",
        "mode": "realtime",
        "endpoint": f"{IMD_BASE_URL}/warnings_district_api.php",
        "auth_env": "IMD_API_TOKEN",
        "description": "District-wise weather warning codes.",
    },
    "imd_district_rainfall_forecast": {
        "source": "IMD",
        "dataset": "State District Rainfall Forecast",
        "mode": "realtime",
        "endpoint": f"{IMD_BASE_URL}/state_district_rainfall_forecast_api.php",
        "auth_env": "IMD_API_TOKEN",
        "description": "Five-day district rainfall forecast.",
    },
    "datagov_configured_resources": {
        "source": "DATA_GOV_IN",
        "dataset": "Configured public OGD resources",
        "mode": "training_context",
        "endpoint": DATAGOV_BASE_URL,
        "auth_env": "DATAGOV_API_KEY",
        "description": "Government Open Data resources selected by resource UUID.",
    },
}


class OnlineDataError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def payload_hash(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _auth_headers(source: str, token: str | None) -> dict[str, str]:
    if not token:
        return {}
    if source == "IMD":
        return {"Authorization": f"Bearer {token}"}
    return {}


def _request_json(
    url: str,
    *,
    source: str,
    token: str | None = None,
    params: Mapping[str, Any] | None = None,
) -> Any:
    try:
        response = httpx.get(
            url,
            params=params,
            headers=_auth_headers(source, token),
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise OnlineDataError(
            f"{source} returned HTTP {exc.response.status_code}: {url}"
        ) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise OnlineDataError(f"Unable to fetch online data: {url}") from exc


def _unwrap_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]

    if isinstance(payload, dict):
        for key in ("records", "data", "result", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
            if isinstance(value, dict):
                nested = _unwrap_records(value)
                if nested:
                    return nested

        if payload and all(isinstance(v, (str, int, float, bool, type(None))) for v in payload.values()):
            return [payload]

    return []


def _district_from_row(row: Mapping[str, Any]) -> str | None:
    for key in (
        "district",
        "District",
        "DISTRICT",
        "District Name",
        "district_name",
    ):
        value = row.get(key)
        if value:
            return str(value).strip().upper()
    return None


def _observed_at_from_row(row: Mapping[str, Any]) -> datetime | None:
    for key in ("Date of Observation", "Date", "date_obs", "DATE"):
        value = row.get(key)
        if not value:
            continue
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
    return None


def persist_records(
    db: Session,
    *,
    source: str,
    dataset: str,
    scope: str,
    records: Iterable[Mapping[str, Any]],
) -> int:
    inserted = 0

    for record in records:
        payload = dict(record)
        digest = payload_hash(payload)
        existing = db.query(ExternalDataObservationDB).filter(
            ExternalDataObservationDB.source == source,
            ExternalDataObservationDB.dataset == dataset,
            ExternalDataObservationDB.payload_hash == digest,
        ).first()

        if existing:
            continue

        row = ExternalDataObservationDB(
            id=f"EXT-{uuid.uuid4().hex[:12]}",
            source=source,
            dataset=dataset,
            scope=scope,
            district=_district_from_row(payload),
            observed_at=_observed_at_from_row(payload),
            source_updated_at=_observed_at_from_row(payload),
            payload=payload,
            payload_hash=digest,
            fetched_at=utc_now(),
            status="INGESTED",
        )
        db.add(row)
        inserted += 1

    if inserted:
        db.commit()

    return inserted


def fetch_datagov_resource(
    db: Session,
    resource_id: str,
    *,
    dataset_name: str | None = None,
    scope: str = "training_context",
    limit: int = 1000,
) -> dict[str, Any]:
    api_key = os.getenv("DATAGOV_API_KEY")
    if not api_key:
        return {
            "status": "AUTH_REQUIRED",
            "source": "DATA_GOV_IN",
            "resource_id": resource_id,
            "records": 0,
        }

    payload = _request_json(
        f"{DATAGOV_BASE_URL}/{resource_id}",
        source="DATA_GOV_IN",
        params={
            "api-key": api_key,
            "format": "json",
            "limit": limit,
        },
    )
    records = _unwrap_records(payload)
    inserted = persist_records(
        db,
        source="DATA_GOV_IN",
        dataset=dataset_name or resource_id,
        scope=scope,
        records=records,
    )

    return {
        "status": "INGESTED",
        "source": "DATA_GOV_IN",
        "resource_id": resource_id,
        "records_received": len(records),
        "records_inserted": inserted,
    }


def fetch_imd_source(
    db: Session,
    source_key: str,
    *,
    params: Mapping[str, Any] | None = None,
    scope: str = "real_time",
) -> dict[str, Any]:
    spec = SOURCE_CATALOG.get(source_key)
    if not spec or spec["source"] != "IMD":
        raise OnlineDataError(f"Unknown IMD source: {source_key}")

    token = os.getenv("IMD_API_TOKEN")
    # IMD API access may require public-IP whitelisting. When a token is not
    # configured, still attempt the documented endpoint for deployments where
    # the network is already permitted.
    payload = _request_json(
        spec["endpoint"],
        source="IMD",
        token=token,
        params=params,
    )
    records = _unwrap_records(payload)
    inserted = persist_records(
        db,
        source="IMD",
        dataset=spec["dataset"],
        scope=scope,
        records=records,
    )

    return {
        "status": "INGESTED",
        "source": "IMD",
        "source_key": source_key,
        "records_received": len(records),
        "records_inserted": inserted,
    }


def latest_context_for_district(
    db: Session,
    district: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = db.query(ExternalDataObservationDB).filter(
        ExternalDataObservationDB.district == district.strip().upper()
    ).order_by(
        ExternalDataObservationDB.fetched_at.desc()
    ).limit(limit).all()

    return [
        {
            "source": row.source,
            "dataset": row.dataset,
            "district": row.district,
            "observed_at": row.observed_at.isoformat() if row.observed_at else None,
            "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
            "status": row.status,
            "payload": row.payload,
        }
        for row in rows
    ]


def configured_datagov_resources() -> list[tuple[str, str]]:
    raw = os.getenv("DATAGOV_RESOURCES", "").strip()
    resources: list[tuple[str, str]] = []

    if not raw:
        return resources

    for item in raw.split(","):
        token = item.strip()
        if not token:
            continue
        if ":" in token:
            resource_id, name = token.split(":", 1)
            resources.append((resource_id.strip(), name.strip() or resource_id.strip()))
        else:
            resources.append((token, token))
    return resources


def refresh_online_data(
    db: Session,
    *,
    realtime: bool = True,
    training_context: bool = True,
) -> dict[str, Any]:
    results = []

    if realtime:
        for source_key in (
            "imd_current_weather",
            "imd_district_rainfall",
            "imd_district_warning",
            "imd_district_rainfall_forecast",
        ):
            try:
                results.append(fetch_imd_source(db, source_key))
            except OnlineDataError as exc:
                results.append({
                    "status": "ERROR",
                    "source_key": source_key,
                    "detail": str(exc),
                })

    if training_context:
        for resource_id, name in configured_datagov_resources():
            try:
                results.append(fetch_datagov_resource(
                    db,
                    resource_id,
                    dataset_name=name,
                    scope="training_context",
                ))
            except OnlineDataError as exc:
                results.append({
                    "status": "ERROR",
                    "source": "DATA_GOV_IN",
                    "resource_id": resource_id,
                    "detail": str(exc),
                })

    return {
        "fetched_at": utc_now().isoformat(),
        "results": results,
        "inserted_total": sum(
            int(result.get("records_inserted", 0))
            for result in results
        ),
    }


def watch_online_data(
    db_factory,
    interval_seconds: int = 900,
) -> None:
    while True:
        db: Session = db_factory()
        try:
            refresh_online_data(db, realtime=True, training_context=True)
        finally:
            db.close()
        time.sleep(max(60, interval_seconds))
