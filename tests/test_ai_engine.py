import pytest

from services.ai.anomaly import MODEL_NAME, MODEL_VERSION, analyze_institution
from services.ai.features import FEATURE_NAMES, FeatureValidationError, extract_features, reference_matrix


REFERENCE = [
    {"attendance": 40 + i, "beneficiaries": 420 + i * 4, "inspections": 4 + (i % 3), "report_variance": 0.03 + i * 0.005, "sanctioned_capacity": 600}
    for i in range(10)
]


def test_feature_contract_is_deterministic():
    payload = {
        "attendance": 45,
        "beneficiaries": 300,
        "inspections": 5,
        "report_variance": 0.04,
        "sanctioned_capacity": 500,
    }
    vector = extract_features(payload)

    assert tuple(FEATURE_NAMES) == (
        "attendance_rate",
        "beneficiary_count",
        "inspection_count",
        "report_variance",
        "capacity_utilization",
    )
    assert vector.shape == (5,)
    assert vector[4] == pytest.approx(0.6)


def test_invalid_feature_payload_is_rejected():
    with pytest.raises(FeatureValidationError):
        extract_features({
            "attendance": 130,
            "beneficiaries": 10,
            "inspections": 1,
            "report_variance": 0.01,
        })


def test_reference_matrix_has_expected_shape():
    matrix = reference_matrix(REFERENCE)
    assert matrix.shape == (10, len(FEATURE_NAMES))


def test_engine_uses_reference_cohort_not_hidden_training_data():
    result = analyze_institution(REFERENCE[0], reference_data=REFERENCE)

    assert result["model_name"] == MODEL_NAME
    assert result["model_version"] == MODEL_VERSION
    assert result["model_status"] == "TRAINED_ON_PEER_COHORT"
    assert result["reference_population_size"] == 10
    assert result["feature_names"] == list(FEATURE_NAMES)
    assert 0 <= result["anomaly_score"] <= 1
    assert 0 <= result["peer_deviation_score"] <= 1
    assert 0 <= result["risk_score"] <= 100


def test_cold_start_has_explicit_model_status():
    result = analyze_institution({
        "attendance": 41,
        "beneficiaries": 58,
        "inspections": 5,
        "report_variance": 0.04,
        "sanctioned_capacity": 60,
    })

    assert result["model_status"] == "INSUFFICIENT_REFERENCE_DATA"
    assert result["reference_population_size"] == 0
    assert 0 <= result["risk_score"] <= 100


def test_high_reporting_variance_triggers_transparent_guardrail():
    result = analyze_institution({
        "attendance": 80,
        "beneficiaries": 70,
        "inspections": 3,
        "report_variance": 0.25,
        "sanctioned_capacity": 100,
    })

    assert result["risk_score"] >= 61
    assert result["risk_band"] == "HIGH"
    assert any(f["metric"] == "Self-Reporting Variance" for f in result["factors"])


def test_cctv_is_not_invented_when_no_count_is_provided():
    result = analyze_institution({
        "attendance": 41,
        "beneficiaries": 58,
        "inspections": 5,
        "report_variance": 0.04,
    })

    assert result["ghost_source"] == "UNAVAILABLE"
    assert result["ghost_beneficiary_score"] == 0.0
