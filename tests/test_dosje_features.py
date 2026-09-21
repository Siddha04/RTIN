import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)

def get_auth_header(email: str = "admin@inspect-ai.local", password: str = "Admin@123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_schemes_summary():
    headers = get_auth_header()
    res = client.get("/api/schemes/summary", headers=headers)
    assert res.status_code == 200
    schemes = res.json()
    assert len(schemes) == 5
    scheme_names = [s["scheme"] for s in schemes]
    assert "DDRS" in scheme_names
    assert "SENIOR_CITIZENS" in scheme_names
    assert "SMILE" in scheme_names
    assert "NMBA" in scheme_names
    assert "PM_AJAY" in scheme_names

def test_cctv_feeds_and_snapshot():
    headers = get_auth_header()
    # List feeds
    res = client.get("/api/cctv/feeds", headers=headers)
    assert res.status_code == 200
    feeds = res.json()
    assert len(feeds) > 0
    feed_id = feeds[0]["id"]

    # Capture snapshot
    snap_res = client.post("/api/cctv/snapshot", json={"feed_id": feed_id}, headers=headers)
    assert snap_res.status_code == 200
    snap_data = snap_res.json()
    assert "sha256_hash" in snap_data
    assert snap_data["status"] == "CAPTURED_AND_HASHED"

def test_vc_candidate_and_session():
    headers = get_auth_header()
    # Pick candidate
    cand_res = client.get("/api/vc/random-candidate?institution_id=INS-001&target_type=BENEFICIARY", headers=headers)
    assert cand_res.status_code == 200
    cand = cand_res.json()
    assert cand["target_type"] == "BENEFICIARY"
    assert "name" in cand

    # Initiate call
    init_res = client.post("/api/vc/initiate", json={
        "institution_id": "INS-001",
        "target_type": "BENEFICIARY",
        "target_name": cand["name"],
        "target_contact": "+91-98765-00000"
    }, headers=headers)
    assert init_res.status_code == 200
    session_data = init_res.json()
    session_id = session_data["session_id"]
    assert "room_code" in session_data

    # Finish call
    finish_res = client.post("/api/vc/finish", json={
        "session_id": session_id,
        "duration_sec": 142,
        "notes": "Walkthrough conducted. Beneficiary present in classroom.",
        "discrepancy_flagged": False
    }, headers=headers)
    assert finish_res.status_code == 200
    assert finish_res.json()["status"] == "COMPLETED"

def test_ai_random_duty_allocation():
    headers = get_auth_header()
    res = client.post("/api/assignment/allocate", json={"target_count": 2, "is_surprise": True}, headers=headers)
    assert res.status_code == 200
    allocations = res.json()
    assert len(allocations) > 0
    for a in allocations:
        assert a["anti_collusion_cleared"] is True
        assert a["is_surprise"] is True

def test_geofence_checkin():
    headers = get_auth_header("inspector@inspect-ai.local", "Inspector@123")
    # INS-001 is at lat=11.6643, lng=78.1460
    # Coordinates within 50 meters
    res_valid = client.post("/api/inspections/INSP-1003/geofence-checkin", json={
        "latitude": 11.6644,
        "longitude": 78.1461
    }, headers=headers)
    assert res_valid.status_code == 200
    assert res_valid.json()["geofence_unlocked"] is True

    # Coordinates far away (> 5 km away)
    res_invalid = client.post("/api/inspections/INSP-1003/geofence-checkin", json={
        "latitude": 12.0000,
        "longitude": 79.0000
    }, headers=headers)
    assert res_invalid.status_code == 200
    assert res_invalid.json()["geofence_unlocked"] is False

def test_ngo_biometric_punch():
    headers = get_auth_header("ngo@inspect-ai.local", "Ngo@123")
    res = client.post("/api/biometric/punch", json={
        "institution_id": "INS-001",
        "shift": "MORNING",
        "staff_present": 6,
        "staff_total": 6,
        "beneficiaries_present": 52,
        "beneficiaries_total": 58,
        "cctv_estimated_headcount": 50
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "SUBMITTED"
