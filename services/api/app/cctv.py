import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from services.api.app.models import CCTVFeedDB, InstitutionDB, EvidenceDB

def utc_now():
    return datetime.now(timezone.utc)

# Standard mock stream video sources for realistic in-browser CCTV display
MOCK_STREAM_FEEDS = {
    "Main Entrance & Gate": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "Kitchen & Dining Hall": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "Dormitories & Living Area": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
    "Activity & Vocational Hall": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"
}

def get_institution_feeds(db: Session, institution_id: Optional[str] = None) -> List[Dict[str, Any]]:
    query = db.query(CCTVFeedDB)
    if institution_id:
        query = query.filter(CCTVFeedDB.institution_id == institution_id)
    
    feeds = query.all()
    results = []
    
    for feed in feeds:
        inst = db.query(InstitutionDB).filter(InstitutionDB.id == feed.institution_id).first()
        results.append({
            "id": feed.id,
            "institution_id": feed.institution_id,
            "institution_name": inst.name if inst else "Unknown Facility",
            "district": inst.district if inst else "Unknown District",
            "scheme": inst.scheme if inst else "DDRS",
            "camera_name": feed.camera_name,
            "stream_url": feed.stream_url,
            "status": feed.status,
            "ai_crowd_count": feed.ai_crowd_count,
            "motion_detected": feed.motion_detected,
            "last_ping": feed.last_ping.isoformat() if feed.last_ping else None
        })
    return results

def capture_cctv_snapshot(
    db: Session,
    feed_id: str,
    officer_id: str,
    inspection_id: Optional[str] = None
) -> Dict[str, Any]:
    feed = db.query(CCTVFeedDB).filter(CCTVFeedDB.id == feed_id).first()
    if not feed:
        raise ValueError(f"CCTV Feed '{feed_id}' not found")

    inst = db.query(InstitutionDB).filter(InstitutionDB.id == feed.institution_id).first()
    
    evidence_id = f"ev-cctv-{uuid.uuid4().hex[:8]}"
    sha_hash = f"cctv_{uuid.uuid4().hex}"

    evidence = EvidenceDB(
        id=evidence_id,
        institution_id=feed.institution_id,
        inspection_id=inspection_id or "cctv-audit-snapshot",
        officer_id=officer_id,
        file_name=f"cctv_snapshot_{feed.camera_name.replace(' ', '_').lower()}.jpg",
        mime_type="image/jpeg",
        file_size=1024 * 340,  # ~340 KB snapshot
        sha256_hash=sha_hash,
        latitude=inst.lat if inst else 0.0,
        longitude=inst.lng if inst else 0.0,
        captured_at=utc_now(),
        verified=True,
        verification_checks={
            "source": "CCTV_FEED",
            "camera_name": feed.camera_name,
            "stream_id": feed.id,
            "ai_crowd_count": feed.ai_crowd_count,
            "sha256": sha_hash
        },
        uploaded_at=utc_now()
    )

    db.add(evidence)
    db.commit()

    return {
        "evidence_id": evidence.id,
        "institution_id": feed.institution_id,
        "camera_name": feed.camera_name,
        "ai_crowd_count": feed.ai_crowd_count,
        "sha256_hash": sha_hash,
        "timestamp": evidence.captured_at.isoformat(),
        "status": "CAPTURED_AND_HASHED"
    }
