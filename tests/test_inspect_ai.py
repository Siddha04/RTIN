import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.ai.anomaly import analyze_institution

client = TestClient(app)

# Helper function to obtain token
def get_auth_headers(email="admin@inspect-ai.local", password="Admin@123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "inspect-ai-api"

def test_auth_login_and_me():
    # Login success
    res = client.post("/api/auth/login", json={"email": "admin@inspect-ai.local", "password": "Admin@123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "ministry"

    # Get Me
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@inspect-ai.local"

def test_auth_invalid_credentials():
    res = client.post("/api/auth/login", json={"email": "admin@inspect-ai.local", "password": "WrongPassword"})
    assert res.status_code == 401

def test_change_password():
    headers = get_auth_headers("ngo@inspect-ai.local", "Ngo@123")
    res = client.post("/api/auth/change-password", json={"old_password": "Ngo@123", "new_password": "NewSecretPassword@123"}, headers=headers)
    assert res.status_code == 200

    # Verify login with new password
    res_new = client.post("/api/auth/login", json={"email": "ngo@inspect-ai.local", "password": "NewSecretPassword@123"})
    assert res_new.status_code == 200

    # Revert password back for consistency
    headers_new = {"Authorization": f"Bearer {res_new.json()['access_token']}"}
    client.post("/api/auth/change-password", json={"old_password": "NewSecretPassword@123", "new_password": "Ngo@123"}, headers=headers_new)

def test_institution_crud():
    # 1. List
    res = client.get("/api/institutions")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 4

    # 2. Create
    payload = {
        "name": "Integration Skill Hub - Thanjavur",
        "district": "Thanjavur",
        "lat": 10.7870,
        "lng": 79.1378,
        "attendance": 88,
        "beneficiaries": 450,
        "inspections": 1,
        "report_variance": 0.22
    }
    create_res = client.post("/api/institutions", json=payload)
    assert create_res.status_code == 200
    new_inst = create_res.json()
    assert new_inst["name"] == payload["name"]
    assert "risk_score" in new_inst

    # 3. Get Detail
    detail_res = client.get(f"/api/institutions/{new_inst['id']}")
    assert detail_res.status_code == 200
    assert detail_res.json()["district"] == "Thanjavur"

    # 4. Update
    patch_res = client.patch(f"/api/institutions/{new_inst['id']}", json={"attendance": 45})
    assert patch_res.status_code == 200
    assert patch_res.json()["attendance"] == 45

    # 5. Delete (Deactivate)
    del_res = client.delete(f"/api/institutions/{new_inst['id']}")
    assert del_res.status_code == 200

def test_ai_anomaly_engine():
    # Test IsolationForest model direct execution
    result = analyze_institution({"attendance": 92, "beneficiaries": 500, "inspections": 2, "report_variance": 0.28})
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_band"] in ["LOW", "MEDIUM", "HIGH"]
    assert isinstance(result["anomaly"], bool)

    # API Trigger
    api_res = client.post("/api/ai/analyze", json={"institution_id": "INS-001"})
    assert api_res.status_code == 200
    assert "risk_score" in api_res.json()

def test_inspection_lifecycle():
    # Create
    create_res = client.post("/api/inspections", json={
        "institution_id": "INS-001",
        "inspector_name": "R. Sharma",
        "priority": True,
        "notes": "Verify attendance registers"
    })
    assert create_res.status_code == 200
    insp_id = create_res.json()["id"]

    # List
    list_res = client.get("/api/inspections")
    assert list_res.status_code == 200
    assert any(i["id"] == insp_id for i in list_res.json())

    # Status Update
    patch_res = client.patch(f"/api/inspections/{insp_id}", json={"status": "completed", "notes": "Audit completed clean"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

def test_evidence_upload_and_verification():
    # Upload File
    files = {"file": ("audit_sample.png", b"fake binary PNG data stream", "image/png")}
    up_res = client.post("/api/evidence/upload", files=files)
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert "sha256" in up_data

    # Verify Metadata
    verify_payload = {
        "institution_id": "INS-001",
        "inspection_id": "INSP-1001",
        "officer_id": "USR-02",
        "latitude": 11.6643,
        "longitude": 78.1460,
        "captured_at": "2026-09-09T10:00:00Z",
        "sha256_hash": up_data["sha256"]
    }
    v_res = client.post("/api/evidence/verify", json=verify_payload)
    assert v_res.status_code == 200
    assert v_res.json()["verified"] is True

def test_alerts_engine():
    res = client.get("/api/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) >= 1

    first_id = alerts[0]["id"]
    ack_res = client.patch(f"/api/alerts/{first_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"

def test_dashboard_summary():
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "institutions" in data
    assert "high_risk" in data
    assert "average_risk" in data

def test_reports_and_export():
    # Summary
    rep_res = client.get("/api/reports/summary")
    assert rep_res.status_code == 200
    assert "total_institutions" in rep_res.json()

    # CSV Export
    csv_res = client.get("/api/reports/export?format=csv")
    assert csv_res.status_code == 200
    assert "Content-Disposition" in csv_res.headers
    assert "text/csv" in csv_res.headers["content-type"]

def test_compliance_summary():
    res = client.get("/api/compliance/summary")
    assert res.status_code == 200
    assert "overall_compliance_rate" in res.json()
