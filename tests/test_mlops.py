import tempfile
from pathlib import Path

import pytest

from services.ai.features import FEATURE_NAMES, extract_features
from services.ai.mlops import (
    drift_report,
    fingerprint_records,
    latest_model_status,
    population_stability_index,
)
from services.ai.supervised import train_xgboost_model
from services.ai.training import train_isolation_forest_model


def sample_records(n=12):
    return [
        {
            "attendance": 40 + (i % 8),
            "beneficiaries": 300 + i * 5,
            "inspections": 3 + (i % 4),
            "report_variance": 0.02 + (i % 6) * 0.01,
            "sanctioned_capacity": 500,
        }
        for i in range(n)
    ]


def test_dataset_fingerprint_is_deterministic():
    a = [{"b": 2, "a": 1}, {"a": 3, "b": 4}]
    b = [{"a": 1, "b": 2}, {"b": 4, "a": 3}]
    assert fingerprint_records(a) == fingerprint_records(b)


def test_population_stability_index_detects_large_shift():
    baseline = list(range(10))
    current = list(range(90, 100))
    assert population_stability_index(baseline, current) > 0.20


def test_drift_report_uses_canonical_features():
    baseline = sample_records(12)
    current = [
        {**row, "attendance": 90 + (i % 5)}
        for i, row in enumerate(sample_records(12))
    ]
    report = drift_report(
        baseline,
        current,
        FEATURE_NAMES,
        extract_features,
        threshold=0.20,
    )
    assert report["status"] == "OK"
    assert "attendance_rate" in report["features"]
    assert report["features"]["attendance_rate"]["psi"] >= 0.0


def test_isolation_forest_artifact_round_trip():
    with tempfile.TemporaryDirectory() as directory:
        metadata = train_isolation_forest_model(
            sample_records(12),
            directory,
        )
        status = latest_model_status(directory)

        assert metadata["model_name"] == "inspect-ai-isolation-forest"
        assert metadata["artifact_sha256"]
        assert status["status"] == "READY"
        assert status["integrity_ok"] is True
        assert Path(metadata["artifact_path"]).exists()


def test_xgboost_rejects_single_class_labels_before_training():
    records = sample_records(20)
    with pytest.raises(ValueError, match="both binary risk outcome classes"):
        train_xgboost_model(records, [0] * 20, tempfile.mkdtemp())
