from types import SimpleNamespace

from services.ai.anomaly import analyze_institution
from services.ai.assignment_optimizer import assign_targets, select_targets
from services.ai.documents import compare_documents, extract_fields
from services.ai.features import FEATURE_NAMES, extract_features
from services.ai.mlops import drift_report


def sample_history():
    return [
        {
            "attendance": 40 + (i % 8),
            "beneficiaries": 300 + i * 4,
            "inspections": 3 + (i % 3),
            "report_variance": 0.02 + (i % 5) * 0.01,
            "sanctioned_capacity": 500,
        }
        for i in range(10)
    ]


def test_final_ml_pipeline_contract():
    history = sample_history()
    current = {
        "attendance": 47,
        "beneficiaries": 332,
        "inspections": 5,
        "report_variance": 0.04,
        "sanctioned_capacity": 500,
        "cctv_headcount": 28,
    }

    risk = analyze_institution(current, reference_data=history)
    assert risk["model_status"] == "TRAINED_ON_PEER_COHORT"
    assert risk["reference_population_size"] == 10
    assert 0 <= risk["risk_score"] <= 100

    drift = drift_report(
        history,
        [{**row, "attendance": row["attendance"] + 30} for row in history],
        FEATURE_NAMES,
        extract_features,
    )
    assert drift["status"] == "OK"
    assert "attendance_rate" in drift["features"]

    fields = extract_fields(
        "Institution ID: INS-001 Attendance Rate: 82.5% "
        "Beneficiaries: 58 Grant Amount: INR 125,000"
    )
    assert fields["institution_id"] == "INS-001"
    assert fields["beneficiary_count"] == 58
    assert fields["grant_amount"] == 125000.0

    consistency = compare_documents([
        fields,
        {**fields, "beneficiary_count": 61},
    ])
    assert consistency["status"] == "CONFLICTS_FOUND"

    institutions = [
        SimpleNamespace(id="INS-001", report_variance=0.22, district="Salem"),
        SimpleNamespace(id="INS-002", report_variance=0.03, district="Erode"),
        SimpleNamespace(id="INS-003", report_variance=0.05, district="Coimbatore"),
    ]
    risk_by_id = {
        "INS-001": SimpleNamespace(risk_score=90, anomaly=True),
        "INS-002": SimpleNamespace(risk_score=40, anomaly=False),
        "INS-003": SimpleNamespace(risk_score=60, anomaly=False),
    }
    targets = select_targets(institutions, risk_by_id, len(institutions))

    inspectors = [
        SimpleNamespace(id="USR-01", assigned_district="Salem", home_district="Chennai"),
    ]
    assignments = assign_targets(
        targets,
        inspectors,
        recent_pairings={("USR-01", "INS-001")},
    )
    assert [row["institution"].id for row in assignments] == ["INS-002", "INS-003"]
