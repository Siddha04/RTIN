"""External context feature extraction and district-level enrichment."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from sqlalchemy.orm import Session

from services.api.app.models import ExternalDataObservationDB

CONTEXT_FEATURE_NAMES = (
    "weather_temperature_c",
    "weather_humidity_pct",
    "weather_rainfall_24h_mm",
    "weather_wind_kmph",
    "weather_warning_score",
    "udid_total_count",
    "deaddiction_centres_count",
)


def _number(payload: Mapping[str, Any], keys: Sequence[str]) -> float | None:
    for key in keys:
        value = payload.get(key)
        if value in (None, ""):
            continue
        try:
            number = float(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            continue
        if number == number and number not in (float("inf"), float("-inf")):
            return number
    return None


def _warning_score(payload: Mapping[str, Any]) -> float:
    text = " ".join(
        str(payload.get(key, ""))
        for key in (
            "warning",
            "warning_text",
            "warning_description",
            "alert",
            "severity",
            "Weather Code",
        )
    ).lower()

    if not text:
        return 0.0

    if any(term in text for term in ("red", "severe", "very heavy", "cyclone", "extreme")):
        return 1.0
    if any(term in text for term in ("orange", "heavy", "thunderstorm", "lightning", "squall")):
        return 0.7
    if any(term in text for term in ("yellow", "moderate", "watch")):
        return 0.4
    return 0.1


def _latest_rows(
    db: Session,
    district: str,
    source: str,
    limit: int = 100,
) -> list[ExternalDataObservationDB]:
    return db.query(ExternalDataObservationDB).filter(
        ExternalDataObservationDB.source == source,
        ExternalDataObservationDB.district == district.strip().upper(),
    ).order_by(
        ExternalDataObservationDB.fetched_at.desc()
    ).limit(limit).all()


def district_context(db: Session, district: str) -> dict[str, float | None]:
    """Aggregate latest external observations into stable district context."""
    result: dict[str, float | None] = {
        name: 0.0 for name in CONTEXT_FEATURE_NAMES
    }

    weather_rows = _latest_rows(db, district, "IMD")
    for row in weather_rows:
        payload = row.payload or {}
        temp = _number(payload, ("Temperature", "temperature", "temp_c", "TEMP"))
        humidity = _number(payload, ("Humidity", "humidity", "relative_humidity"))
        rain = _number(payload, ("Last 24 hrs Rainfall", "rainfall_24h_mm", "rainfall"))
        wind = _number(payload, ("Wind Speed", "wind_speed", "wind_kmph"))

        if temp is not None and result["weather_temperature_c"] == 0.0:
            result["weather_temperature_c"] = temp
        if humidity is not None and result["weather_humidity_pct"] == 0.0:
            result["weather_humidity_pct"] = humidity
        if rain is not None and result["weather_rainfall_24h_mm"] == 0.0:
            result["weather_rainfall_24h_mm"] = rain
        if wind is not None and result["weather_wind_kmph"] == 0.0:
            result["weather_wind_kmph"] = wind

        result["weather_warning_score"] = max(
            float(result["weather_warning_score"] or 0.0),
            _warning_score(payload),
        )

    public_rows = _latest_rows(db, district, "DATA_GOV_IN")
    for row in public_rows:
        payload = row.payload or {}
        dataset = row.dataset.lower()

        total = _number(
            payload,
            ("total_count", "Total Number", "total", "beneficiaries", "count"),
        )
        if "udid" in dataset and total is not None:
            result["udid_total_count"] = max(
                float(result["udid_total_count"] or 0.0),
                total,
            )

        centres = _number(
            payload,
            ("de_addiction_centres", "ddacs", "centres", "center_count", "count"),
        )
        if "addiction" in dataset or "de-addiction" in dataset or "ddac" in dataset:
            if centres is not None:
                result["deaddiction_centres_count"] = max(
                    float(result["deaddiction_centres_count"] or 0.0),
                    centres,
                )

    return {
        key: round(float(value or 0.0), 6)
        for key, value in result.items()
    }


def merge_training_context(
    db: Session,
    records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Add external context to RTIN records without manufacturing labels."""
    enriched = []
    cache: dict[str, dict[str, float | None]] = {}

    for record in records:
        item = dict(record)
        district = str(record.get("district") or "").strip().upper()
        if district:
            cache.setdefault(district, district_context(db, district))
            item.update(cache[district])
        enriched.append(item)

    return enriched
