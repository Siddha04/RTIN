"""Database-backed AI history and peer-cohort construction."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from services.api.app.models import InstitutionDB, InstitutionMetricDB

MAX_REFERENCE_ROWS = 200


def _as_record(row: InstitutionMetricDB) -> dict[str, Any]:
    return {
        "attendance": row.attendance,
        "beneficiaries": row.beneficiaries,
        "inspections": row.inspections,
        "report_variance": row.report_variance,
        "sanctioned_capacity": row.sanctioned_capacity,
    }


def build_peer_reference(
    db: Session,
    institution: InstitutionDB,
    limit: int = MAX_REFERENCE_ROWS,
) -> tuple[list[dict[str, Any]], str]:
    """Build a peer cohort from persisted observations.

    Historical observations from the same scheme are preferred. If too few
    exist, observations from all active institutions are added. The current
    institution's own row is excluded from the current-state fallback.
    """
    rows = (
        db.query(InstitutionMetricDB)
        .filter(
            InstitutionMetricDB.scheme == institution.scheme,
            InstitutionMetricDB.institution_id != institution.id,
        )
        .order_by(InstitutionMetricDB.recorded_at.desc())
        .limit(limit)
        .all()
    )
    reference = [_as_record(row) for row in rows]
    scope = f"HISTORY:{institution.scheme}"

    if len(reference) < limit:
        fallback_rows = (
            db.query(InstitutionMetricDB)
            .filter(
                InstitutionMetricDB.scheme != institution.scheme,
                InstitutionMetricDB.institution_id != institution.id,
            )
            .order_by(InstitutionMetricDB.recorded_at.desc())
            .limit(limit - len(reference))
            .all()
        )
        reference.extend(_as_record(row) for row in fallback_rows)
        if fallback_rows:
            scope = "HISTORY:MULTI_SCHEME"

    if len(reference) < 8:
        current_rows = (
            db.query(InstitutionDB)
            .filter(
                InstitutionDB.status == "active",
                InstitutionDB.id != institution.id,
            )
            .limit(limit - len(reference))
            .all()
        )
        reference.extend(
            {
                "attendance": row.attendance,
                "beneficiaries": row.beneficiaries,
                "inspections": row.inspections,
                "report_variance": row.report_variance,
                "sanctioned_capacity": row.sanctioned_capacity,
            }
            for row in current_rows
        )
        if current_rows and not rows:
            scope = "CURRENT_ACTIVE_INSTITUTIONS"

    return reference[:limit], scope


def record_snapshot(
    db: Session,
    institution: InstitutionDB,
    *,
    source: str = "SYSTEM",
    cctv_headcount: int | None = None,
    outcome_label: int | None = None,
) -> InstitutionMetricDB:
    row = InstitutionMetricDB(
        institution_id=institution.id,
        scheme=institution.scheme,
        attendance=float(institution.attendance),
        beneficiaries=int(institution.beneficiaries),
        inspections=int(institution.inspections),
        report_variance=float(institution.report_variance),
        sanctioned_capacity=int(institution.sanctioned_capacity or 0),
        cctv_headcount=cctv_headcount,
        outcome_label=outcome_label,
        source=source,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
