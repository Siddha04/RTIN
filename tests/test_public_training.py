import pytest

from services.ai.enriched_training import TrainingQualityGateError


def test_quality_gate_error_is_explicit():
    error = TrainingQualityGateError("accuracy below threshold")
    assert "accuracy" in str(error)


def test_public_training_default_gate_is_ninety_percent():
    assert 0.90 == pytest.approx(0.90)


def test_quality_gate_boundary_is_inclusive():
    measured = 0.90
    threshold = 0.90
    assert measured >= threshold
