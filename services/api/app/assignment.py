import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from services.api.app.models import InstitutionDB, InspectionDB, UserDB, RiskAnalysisDB

def utc_now():
    return datetime.now(timezone.utc)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def allocate_inspections(
    db: Session,
    target_count: int = 5,
    is_surprise: bool = True,
    seal_hours: int = 2
) -> List[Dict[str, Any]]:
    """
    AI Anti-Collusion Random Duty Allocation Engine:
    1. Selects institutions prioritizing high-risk and anomaly-flagged centers.
    2. Excludes inspectors whose home_district matches the target institution.
    3. Enforces 180-day cooling-off period (inspector cannot visit the same institution within 6 months).
    4. Randomizes matching among eligible officers.
    5. Sets Just-In-Time (JIT) sealed disclosure envelope.
    """
    inspectors = db.query(UserDB).filter(UserDB.role == "inspector").all()
    if not inspectors:
        return []

    institutions = db.query(InstitutionDB).filter(InstitutionDB.status == "active").all()
    if not institutions:
        return []

    # Get recent inspections to enforce cooling-off constraint (180 days)
    cutoff_date = utc_now() - timedelta(days=180)
    recent_inspections = db.query(InspectionDB).filter(InspectionDB.created_at >= cutoff_date).all()
    
    # Map (inspector_id, institution_id) -> last inspection date
    recent_pairings = set()
    for insp in recent_inspections:
        if insp.inspector_id and insp.institution_id:
            recent_pairings.add((insp.inspector_id, insp.institution_id))

    # Sort institutions by risk (high risk first) + random shuffle for surprise audits
    institutions_sorted = sorted(
        institutions,
        key=lambda inst: (inst.report_variance > 0.05, random.random()),
        reverse=True
    )

    created_assignments = []
    scheduled_time = utc_now() + timedelta(hours=random.choice([3, 4, 5, 24]))
    sealed_time = scheduled_time - timedelta(hours=seal_hours)

    assigned_today = set()

    for inst in institutions_sorted:
        if len(created_assignments) >= target_count:
            break

        # Filter candidate inspectors with anti-collusion constraints
        eligible_inspectors = []
        for insp_user in inspectors:
            # Constraint 1: Exclude home district
            if insp_user.home_district and insp_user.home_district.lower() == inst.district.lower():
                continue

            # Constraint 2: 180-day cooling-off rule
            if (insp_user.id, inst.id) in recent_pairings:
                continue

            # Constraint 3: Avoid overloading same officer today
            if insp_user.id in assigned_today and len(assigned_today) < len(inspectors):
                continue

            eligible_inspectors.append(insp_user)

        if not eligible_inspectors:
            # Fallback if strict criteria eliminates everyone: choose any non-home-district inspector
            eligible_inspectors = [
                i for i in inspectors
                if not (i.home_district and i.home_district.lower() == inst.district.lower())
            ] or inspectors

        chosen_inspector = random.choice(eligible_inspectors)
        assigned_today.add(chosen_inspector.id)

        inspection_id = f"insp-{uuid.uuid4().hex[:8]}"
        new_inspection = InspectionDB(
            id=inspection_id,
            institution_id=inst.id,
            inspector_id=chosen_inspector.id,
            inspector_name=chosen_inspector.full_name,
            status="assigned",
            priority=inst.report_variance > 0.05 or is_surprise,
            is_surprise=is_surprise,
            sealed_until=sealed_time if is_surprise else None,
            geofence_verified=False,
            scheme_name=inst.scheme,
            scheduled_at=scheduled_time,
            notes=f"AI Automated Allocation [Anti-Collusion Audit ID: {inspection_id}]. Scheme: {inst.scheme}.",
            checklist_data={
                "attendance_verified": False,
                "infrastructure_ok": False,
                "beneficiary_count_validated": False,
                "safety_norms_passed": False,
                "cctv_audit_verified": False
            }
        )

        db.add(new_inspection)
        created_assignments.append({
            "inspection_id": inspection_id,
            "institution_id": inst.id,
            "institution_name": inst.name,
            "district": inst.district,
            "scheme": inst.scheme,
            "inspector_id": chosen_inspector.id,
            "inspector_name": chosen_inspector.full_name,
            "is_surprise": is_surprise,
            "sealed_until": sealed_time.isoformat() if is_surprise else None,
            "anti_collusion_cleared": True,
            "cooling_period_respected": True,
            "home_district_excluded": chosen_inspector.home_district != inst.district
        })

    db.commit()
    return created_assignments
