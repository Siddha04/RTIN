from services.ai.anomaly import analyze_institution
from services.api.app.database import Base, engine, SessionLocal
from services.api.app.models import InstitutionDB, InstitutionMetricDB


def test_phase2_engine_accepts_persisted_peer_observations():
    payload = {
        "attendance": 45,
        "beneficiaries": 310,
        "inspections": 5,
        "report_variance": 0.04,
        "sanctioned_capacity": 500,
    }
    reference = [
        {
            "attendance": 40 + i,
            "beneficiaries": 300 + i * 3,
            "inspections": 4 + (i % 2),
            "report_variance": 0.03 + i * 0.002,
            "sanctioned_capacity": 500,
        }
        for i in range(10)
    ]
    result = analyze_institution(payload, reference_data=reference)
    assert result["model_status"] == "TRAINED_ON_PEER_COHORT"
    assert result["reference_population_size"] == 10


def test_institution_metric_table_exists():
    assert InstitutionMetricDB.__tablename__ == "institution_metrics"


def test_snapshot_fields_are_model_compatible():
    row = InstitutionMetricDB(
        institution_id="TEST",
        scheme="DDRS",
        attendance=50.0,
        beneficiaries=40,
        inspections=2,
        report_variance=0.05,
        sanctioned_capacity=50,
        source="TEST",
    )
    assert row.scheme == "DDRS"
    assert row.source == "TEST"
