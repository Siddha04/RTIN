from datetime import datetime, timezone
import os
import re
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from services.api.app.models import CCTVFeedDB, InstitutionDB, EvidenceDB
from services.ai.vision import (
    VisionCaptureError,
    VisionDependencyError,
    capture_frame,
    demo_frame,
    sha256_bytes,
)

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)


def utc_now():
    return datetime.now(timezone.utc)


def _safe_camera_name(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip().lower())
    return value.strip("_") or "camera"


def get_institution_feeds(
    db: Session,
    institution_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
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
            "last_ping": feed.last_ping.isoformat() if feed.last_ping else None,
        })
    return results


def capture_cctv_snapshot(
    db: Session,
    feed_id: str,
    officer_id: str,
    inspection_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Capture real CCTV bytes and persist a cryptographic evidence record."""
    feed = db.query(CCTVFeedDB).filter(CCTVFeedDB.id == feed_id).first()
    if not feed:
        raise ValueError(f"CCTV Feed '{feed_id}' not found")

    inst = db.query(InstitutionDB).filter(InstitutionDB.id == feed.institution_id).first()
    if not inst:
        raise ValueError(f"Institution '{feed.institution_id}' not found")

    try:
        payload, capture_meta = capture_frame(feed.stream_url)
    except (VisionDependencyError, VisionCaptureError) as exc:
        if os.getenv("RTIN_ALLOW_DEMO_CCTV", "0") == "1":
            payload, capture_meta = demo_frame()
            capture_meta["fallback_reason"] = str(exc)
        else:
            raise ValueError(f"CCTV capture failed: {exc}") from exc

    evidence_id = f"ev-cctv-{uuid.uuid4().hex[:8]}"
    digest = sha256_bytes(payload)
    filename = f"cctv_snapshot_{_safe_camera_name(feed.camera_name)}_{evidence_id}.jpg"
    storage_path = os.path.join(UPLOAD_DIR, filename)

    with open(storage_path, "wb") as handle:
        handle.write(payload)

    evidence = EvidenceDB(
        id=evidence_id,
        institution_id=feed.institution_id,
        inspection_id=inspection_id or "cctv-audit-snapshot",
        officer_id=officer_id,
        file_name=filename,
        mime_type="image/jpeg",
        file_size=len(payload),
        storage_path=storage_path,
        sha256_hash=digest,
        latitude=inst.lat,
        longitude=inst.lng,
        captured_at=utc_now(),
        verified=True,
        verification_checks={
            "source": "CCTV_FEED",
            "camera_name": feed.camera_name,
            "stream_id": feed.id,
            "capture_mode": capture_meta["capture_mode"],
            "sha256_integrity": True,
            "sha256": digest,
        },
        uploaded_at=utc_now(),
    )

    db.add(evidence)
    db.commit()

    return {
        "evidence_id": evidence.id,
        "institution_id": feed.institution_id,
        "camera_name": feed.camera_name,
        "sha256_hash": digest,
        "file_size": len(payload),
        "capture_mode": capture_meta["capture_mode"],
        "timestamp": evidence.captured_at.isoformat(),
        "status": "CAPTURED_AND_HASHED",
    }
