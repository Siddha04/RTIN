import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from services.api.app.models import InstitutionDB, InspectionDB, UserDB, RiskAnalysisDB
from services.ai.assignment_optimizer import assign_targets, select_targets


def utc_now():
    return datetime.now(timezone.utc)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def allocate_inspections(
    db: Session,
    target_count: int = 5,
    is_surprise: bool = True,
    seal_hours: int = 2,
) -> List[Dict[str, Any]]:
    """Risk-aware deterministic allocation with hard anti-collusion constraints."""
    inspectors = db.query(UserDB).filter(UserDB.role == "inspector").all()
    institutions = db.query(InstitutionDB).filter(
        InstitutionDB.status == "active"
    ).all()

    if not inspectors or not institutions or target_count <= 0:
        return []

    risk_records = db.query(RiskAnalysisDB).all()
    risk_by_institution = {str(row.institution_id): row for row in risk_records}

    # Rank the full candidate pool first. Eligibility constraints such as
    # cooling periods can remove high-risk targets; assigning only the top-N
    # before applying constraints could otherwise return zero assignments.
    targets = select_targets(
        institutions=institutions,
        risk_by_institution=risk_by_institution,
        target_count=len(institutions),
    )

    cutoff_date = utc_now() - timedelta(days=180)
    recent_inspections = db.query(InspectionDB).filter(
        InspectionDB.created_at >= cutoff_date
    ).all()
    recent_pairings = {
        (str(row.inspector_id), str(row.institution_id))
        for row in recent_inspections
        if row.inspector_id and row.institution_id
    }

    selections = assign_targets(targets, inspectors, recent_pairings)
    selections = selections[:target_count]
    scheduled_time = utc_now() + timedelta(hours=4)
    sealed_time = scheduled_time - timedelta(hours=seal_hours)

    results: list[dict[str, Any]] = []

    for selected in selections:
        institution = selected["institution"]
        inspector = selected["inspector"]
        inspection_id = f"insp-{uuid.uuid4().hex[:8]}"
        risk_score = float(
            getattr(risk_by_institution.get(str(institution.id)), "risk_score", 0.0)
            or 0.0
        )

        new_inspection = InspectionDB(
            id=inspection_id,
            institution_id=institution.id,
            inspector_id=inspector.id,
            inspector_name=inspector.full_name,
            status="assigned",
            priority=bool(is_surprise or risk_score >= 61),
            is_surprise=is_surprise,
            sealed_until=sealed_time if is_surprise else None,
            geofence_verified=False,
            scheme_name=institution.scheme,
            scheduled_at=scheduled_time,
            notes=(
                "AI Risk-Aware Allocation. "
                f"Target: {selected['target_reason']}. "
                f"Inspector: {selected['pair_reason']}."
            ),
            checklist_data={
                "attendance_verified": False,
                "infrastructure_ok": False,
                "beneficiary_count_validated": False,
                "safety_norms_passed": False,
                "cctv_audit_verified": False,
            },
        )
        db.add(new_inspection)

        results.append({
            "inspection_id": inspection_id,
            "institution_id": institution.id,
            "institution_name": institution.name,
            "district": institution.district,
            "scheme": institution.scheme,
            "inspector_id": inspector.id,
            "inspector_name": inspector.full_name,
            "risk_score": risk_score,
            "allocation_target_score": selected["target_score"],
            "allocation_reason": selected["target_reason"],
            "inspector_selection_score": selected["pair_score"],
            "inspector_selection_reason": selected["pair_reason"],
            "is_surprise": is_surprise,
            "sealed_until": sealed_time.isoformat() if is_surprise else None,
            "anti_collusion_cleared": True,
            "cooling_period_respected": (
                (str(inspector.id), str(institution.id)) not in recent_pairings
            ),
            "home_district_excluded": (
                not (
                    inspector.home_district
                    and institution.district
                    and inspector.home_district.lower() == institution.district.lower()
                )
            ),
        })

    db.commit()
    return results
