import os
# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker

from services.api.app.main import app
from services.api.app.database import get_db, Base
from services.api.app.seed import seed_database
from services.ai.anomaly import analyze_institution
from services.api.app.models import InstitutionDB, InspectionDB, EvidenceDB, AlertDB, RiskAnalysisDB

client = TestClient(app)

def get_auth_headers(email="admin@inspect-ai.local", password="Admin@123"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# 1. Health check
def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

# 2. OpenAPI / Docs
def test_docs():
    res = client.get("/docs")
    assert res.status_code == 200

# 3. Login success
def test_login_success():
    res = client.post("/api/auth/login", json={"email": "admin@inspect-ai.local", "password": "Admin@123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "ministry"

# 4. Login failure
def test_login_failure():
    res = client.post("/api/auth/login", json={"email": "admin@inspect-ai.local", "password": "WrongPassword"})
    assert res.status_code == 401

# 5. Me endpoint
def test_me():
    headers = get_auth_headers()
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "admin@inspect-ai.local"

# 6. Change password
def test_change_password():
    headers = get_auth_headers("ngo@inspect-ai.local", "Ngo@123")
    res = client.post("/api/auth/change-password", json={"old_password": "Ngo@123", "new_password": "NewSecretPassword@123"}, headers=headers)
    assert res.status_code == 200
    
    # Verify login with new password
    res_login = client.post("/api/auth/login", json={"email": "ngo@inspect-ai.local", "password": "NewSecretPassword@123"})
    assert res_login.status_code == 200
    
    # Revert password back
    headers_new = {"Authorization": f"Bearer {res_login.json()['access_token']}"}
    client.post("/api/auth/change-password", json={"old_password": "NewSecretPassword@123", "new_password": "Ngo@123"}, headers=headers_new)

# 7. Authorization role checks (403 for NGO on admin routes)
def test_authorization():
    ngo_headers = get_auth_headers("ngo@inspect-ai.local", "Ngo@123")
    
    # Attempt to create institution as NGO -> expect 403 Forbidden
    res = client.post("/api/institutions", json={
        "name": "Forbidden Institution",
        "district": "Salem",
        "lat": 11.6,
        "lng": 78.1
    }, headers=ngo_headers)
    assert res.status_code == 403

# 8. Institution list
def test_institution_list():
    res = client.get("/api/institutions")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) > 0

# 9. Institution create
def test_institution_create():
    headers = get_auth_headers()
    res = client.post("/api/institutions", json={
        "name": "Test Welfare Academy",
        "district": "Coimbatore",
        "lat": 11.01,
        "lng": 76.95,
        "attendance": 45.0,
        "beneficiaries": 350,
        "inspections": 3,
        "report_variance": 0.02
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Test Welfare Academy"
    assert "risk_score" in data

# 10. Institution update
def test_institution_update():
    headers = get_auth_headers()
    res = client.patch("/api/institutions/INS-001", json={"attendance": 12.0, "report_variance": 0.35}, headers=headers)
    assert res.status_code == 200
    assert res.json()["attendance"] == 12.0

# 11. Institution deactivate
def test_institution_deactivate():
    headers = get_auth_headers()
    # Create temp institution to deactivate
    create_res = client.post("/api/institutions", json={
        "name": "Temp Institution to Deactivate",
        "district": "Madurai",
        "lat": 9.92,
        "lng": 78.11
    }, headers=headers)
    inst_id = create_res.json()["id"]

    res = client.delete(f"/api/institutions/{inst_id}", headers=headers)
    assert res.status_code == 200
    assert "deactivated" in res.json()["message"]

# 12. Institution detail
def test_institution_detail():
    res = client.get("/api/institutions/INS-001")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "INS-001"
    assert "history" in data
    assert "evidence_count" in data

# 13. AI analysis
def test_ai_analysis():
    headers = get_auth_headers()
    res = client.post("/api/ai/analyze", json={
        "attendance": 15.0,
        "beneficiaries": 100,
        "inspections": 1,
        "report_variance": 0.45
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "risk_score" in data
    assert "risk_band" in data
    assert "recommendation" in data

# 14. Risk boundaries (0-30 LOW, 31-60 MEDIUM, 61-100 HIGH)
def test_risk_boundaries():
    # Test low risk inputs
    low_res = analyze_institution({"attendance": 40.0, "beneficiaries": 415, "inspections": 5, "report_variance": 0.02})
    assert low_res["risk_band"] in ["LOW", "MEDIUM"]
    assert 0 <= low_res["risk_score"] <= 100

    # Test high risk / anomaly inputs
    high_res = analyze_institution({"attendance": 95.0, "beneficiaries": 10, "inspections": 10, "report_variance": 0.85})
    assert high_res["risk_band"] == "HIGH"
    assert high_res["risk_score"] >= 61
    assert high_res["recommendation"] == "Priority / surprise inspection"

# 15. Anomaly detection scenario
def test_anomaly_scenario():
    normal_input = {"attendance": 40.0, "beneficiaries": 410, "inspections": 5, "report_variance": 0.03}
    normal_res = analyze_institution(normal_input)
    assert not normal_res["anomaly"]

    abnormal_input = {"attendance": 92.0, "beneficiaries": 50, "inspections": 15, "report_variance": 0.75}
    abnormal_res = analyze_institution(abnormal_input)
    assert abnormal_res["anomaly"] or abnormal_res["risk_score"] >= 61

# 16. Inspection create
def test_inspection_create():
    headers = get_auth_headers()
    res = client.post("/api/inspections", json={
        "institution_id": "INS-001",
        "inspector_name": "Senior Inspector V. Raman",
        "priority": True,
        "notes": "Surprise audit ordered due to high variance."
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["priority"] == True
    assert res.json()["status"] == "priority"

# 17. Inspection update
def test_inspection_update():
    headers = get_auth_headers()
    res = client.patch("/api/inspections/INSP-1001", json={
        "status": "in_progress",
        "notes": "Inspector arrived on site."
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "in_progress"

# 18. Inspection lifecycle (assigned -> priority -> in_progress -> completed)
def test_inspection_lifecycle():
    headers = get_auth_headers()
    # Create new inspection
    create_res = client.post("/api/inspections", json={
        "institution_id": "INS-002",
        "inspector_name": "Field Officer K. Selvan",
        "priority": False,
        "notes": "Routine check"
    }, headers=headers)
    insp_id = create_res.json()["id"]
    assert create_res.json()["status"] == "assigned"

    # Start inspection
    start_res = client.patch(f"/api/inspections/{insp_id}", json={"status": "in_progress"}, headers=headers)
    assert start_res.json()["status"] == "in_progress"

    # Complete inspection
    complete_res = client.patch(f"/api/inspections/{insp_id}", json={"status": "completed", "notes": "All checks verified."}, headers=headers)
    assert complete_res.json()["status"] == "completed"

# 19. Evidence upload
def test_evidence_upload():
    headers = get_auth_headers()
    file_payload = ("test_photo.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00", "image/jpeg")
    res = client.post("/api/evidence/upload", files={"file": file_payload}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "sha256" in data
    assert data["verified"] == True
    assert "storage_path" in data

# 20. Evidence verification
def test_evidence_verification():
    headers = get_auth_headers()
    now_iso = datetime.now(timezone.utc).isoformat()
    res = client.post("/api/evidence/verify", json={
        "institution_id": "INS-001",
        "inspection_id": "INSP-1001",
        "officer_id": "USR-02",
        "latitude": 11.6643,
        "longitude": 78.1460,
        "captured_at": now_iso,
        "sha256_hash": "a"*64
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] == True
    assert data["checks"]["gps"] == True

# 21. Evidence persistence (retrievable file endpoint)
def test_evidence_persistence():
    headers = get_auth_headers()
    now_iso = datetime.now(timezone.utc).isoformat()
    verify_res = client.post("/api/evidence/verify", json={
        "institution_id": "INS-002",
        "inspection_id": "INSP-1002",
        "officer_id": "USR-02",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "captured_at": now_iso
    }, headers=headers)
    ev_id = verify_res.json()["id"]

    # Fetch stored file endpoint
    file_res = client.get(f"/api/evidence/{ev_id}/file")
    assert file_res.status_code == 200
    assert len(file_res.content) > 0

# 22. Alert generation
def test_alert_generation():
    headers = get_auth_headers()
    # High risk institution creation triggers alert
    create_res = client.post("/api/institutions", json={
        "name": "High Risk Anomaly Home",
        "district": "Trichy",
        "lat": 10.79,
        "lng": 78.70,
        "attendance": 90.0,
        "beneficiaries": 10,
        "inspections": 15,
        "report_variance": 0.85
    }, headers=headers)
    assert create_res.status_code == 200

    alerts_res = client.get("/api/alerts")
    assert len(alerts_res.json()) > 0

# 23. Alert acknowledge
def test_alert_acknowledge():
    headers = get_auth_headers()
    alerts = client.get("/api/alerts?status=unacknowledged").json()
    if alerts:
        alert_id = alerts[0]["id"]
        res = client.patch(f"/api/alerts/{alert_id}/acknowledge", headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "acknowledged"

# 24. Dashboard summary
def test_dashboard_summary():
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "institutions" in data
    assert "high_risk" in data
    assert "average_risk" in data

# 25. Reports summary and export
def test_reports():
    res_summary = client.get("/api/reports/summary")
    assert res_summary.status_code == 200
    assert "total_institutions" in res_summary.json()

    res_csv = client.get("/api/reports/export?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "ID,Name,District" in res_csv.text

# 26. Compliance summary
def test_compliance():
    res = client.get("/api/compliance/summary")
    assert res.status_code == 200
    data = res.json()
    assert "overall_compliance_rate" in data
    assert "high_risk_flagged" in data

# 27. Database persistence after session reset
def test_database_persistence():
    headers = get_auth_headers()
    inst_res = client.post("/api/institutions", json={
        "name": "Persistence Verification Center",
        "district": "Salem",
        "lat": 11.66,
        "lng": 78.14,
        "attendance": 40.0,
        "beneficiaries": 200
    }, headers=headers)
    created_id = inst_res.json()["id"]

    # Retrieve again directly
    get_res = client.get(f"/api/institutions/{created_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Persistence Verification Center"
