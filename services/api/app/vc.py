import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from services.api.app.models import VCSessionDB, InstitutionDB, BeneficiaryDB, AlertDB

def utc_now():
    return datetime.now(timezone.utc)

SAMPLE_STAFF = [
    {"name": "Dr. Rajesh Sharma", "role": "Resident Medical Officer", "phone": "+91-98112-34001"},
    {"name": "Anita Verma", "role": "Head Warden & Caregiver", "phone": "+91-98112-34002"},
    {"name": "Suresh Patel", "role": "Special Educator / Counselor", "phone": "+91-98112-34003"},
    {"name": "Meenakshi Sundaram", "role": "Nutrition & Mess Supervisor", "phone": "+91-98112-34004"},
]

def pick_random_candidate(
    db: Session,
    institution_id: str,
    target_type: str = "BENEFICIARY"
) -> Dict[str, Any]:
    inst = db.query(InstitutionDB).filter(InstitutionDB.id == institution_id).first()
    if not inst:
        raise ValueError("Institution not found")

    if target_type == "INCHARGE":
        return {
            "target_type": "INCHARGE",
            "name": inst.contact_person or "Project Incharge",
            "role": "Project Director / Incharge",
            "contact": inst.contact_phone or "+91-9876543210",
            "institution_id": inst.id,
            "institution_name": inst.name,
            "scheme": inst.scheme
        }

    elif target_type == "STAFF":
        staff_member = random.choice(SAMPLE_STAFF)
        return {
            "target_type": "STAFF",
            "name": staff_member["name"],
            "role": staff_member["role"],
            "contact": staff_member["phone"],
            "institution_id": inst.id,
            "institution_name": inst.name,
            "scheme": inst.scheme
        }

    else:  # BENEFICIARY
        beneficiaries = db.query(BeneficiaryDB).filter(BeneficiaryDB.institution_id == institution_id).all()
        if beneficiaries:
            chosen = random.choice(beneficiaries)
            return {
                "target_type": "BENEFICIARY",
                "name": chosen.full_name,
                "role": f"Beneficiary ({chosen.category})",
                "contact": chosen.contact_number or "+91-98000-00000",
                "aadhaar_masked": chosen.aadhaar_masked,
                "institution_id": inst.id,
                "institution_name": inst.name,
                "scheme": inst.scheme
            }
        else:
            return {
                "target_type": "BENEFICIARY",
                "name": "Ram Kumar (Sample Resident)",
                "role": "Enrolled Beneficiary",
                "contact": "+91-98765-43200",
                "aadhaar_masked": "XXXX-XXXX-4912",
                "institution_id": inst.id,
                "institution_name": inst.name,
                "scheme": inst.scheme
            }

def initiate_vc_call(
    db: Session,
    caller_id: str,
    caller_name: str,
    institution_id: str,
    target_type: str,
    target_name: str,
    target_contact: Optional[str] = None
) -> Dict[str, Any]:
    inst = db.query(InstitutionDB).filter(InstitutionDB.id == institution_id).first()
    session_id = f"vc-{uuid.uuid4().hex[:8]}"
    room_code = f"DOSJE-{uuid.uuid4().hex[:6].upper()}"

    session = VCSessionDB(
        id=session_id,
        caller_id=caller_id,
        caller_name=caller_name,
        institution_id=institution_id,
        institution_name=inst.name if inst else "Unknown Facility",
        target_type=target_type,
        target_name=target_name,
        target_contact=target_contact,
        room_code=room_code,
        status="CONNECTED",
        duration_sec=0,
        watermark_data={
            "session_id": session_id,
            "room_code": room_code,
            "gps_lat": inst.lat if inst else 0.0,
            "gps_lng": inst.lng if inst else 0.0,
            "scheme": inst.scheme if inst else "DDRS",
            "initiated_at": utc_now().isoformat(),
            "sha256": f"vc_{uuid.uuid4().hex}"
        },
        notes="",
        created_at=utc_now()
    )

    db.add(session)
    db.commit()

    return {
        "session_id": session.id,
        "room_code": session.room_code,
        "institution_id": institution_id,
        "institution_name": session.institution_name,
        "target_type": target_type,
        "target_name": target_name,
        "status": session.status,
        "watermark": session.watermark_data
    }

def finish_vc_call(
    db: Session,
    session_id: str,
    duration_sec: int,
    notes: str,
    discrepancy_flagged: bool = False
) -> Dict[str, Any]:
    session = db.query(VCSessionDB).filter(VCSessionDB.id == session_id).first()
    if not session:
        raise ValueError(f"VC Session '{session_id}' not found")

    session.status = "COMPLETED"
    session.duration_sec = duration_sec
    session.notes = notes

    if discrepancy_flagged:
        # Create an automatic alert for DoSJE
        alert = AlertDB(
            id=f"alt-vc-{uuid.uuid4().hex[:6]}",
            institution_id=session.institution_id,
            institution_name=session.institution_name,
            type="high_risk",
            severity="high",
            message=f"Discrepancy flagged during Surprise VC with {session.target_name} ({session.target_type}): {notes}",
            status="unacknowledged",
            created_at=utc_now()
        )
        db.add(alert)

    db.commit()

    return {
        "session_id": session.id,
        "status": session.status,
        "duration_sec": session.duration_sec,
        "notes": session.notes,
        "discrepancy_flagged": discrepancy_flagged
    }
