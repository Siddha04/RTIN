from fastapi.testclient import TestClient

from services.api.app.main import app

client = TestClient(app)


def auth_headers():
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@inspect-ai.local", "password": "Admin@123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_model_status_endpoint():
    response = client.get("/api/ai/model/status", headers=auth_headers())
    assert response.status_code == 200
    assert "status" in response.json()


def test_drift_endpoint():
    headers = auth_headers()
    baseline = [
        {
            "attendance": 40 + i,
            "beneficiaries": 300 + i,
            "inspections": 3,
            "report_variance": 0.03,
            "sanctioned_capacity": 500,
        }
        for i in range(10)
    ]
    current = [
        {
            **row,
            "attendance": 80 + (i % 5),
        }
        for i, row in enumerate(baseline)
    ]
    response = client.post(
        "/api/ai/monitor/drift",
        json={"baseline": baseline, "current": current},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert "attendance_rate" in data["features"]
