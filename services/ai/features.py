"""Feature engineering and validation for the INSPECT-AI risk engine.

The feature layer is deliberately independent from the database and API so that
the same transformations can be reused during training, inference, and tests.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

FEATURE_NAMES = (
    "attendance_rate",
    "beneficiary_count",
    "inspection_count",
    "report_variance",
    "capacity_utilization",
)

MIN_REFERENCE_ROWS = 8


class FeatureValidationError(ValueError):
    """Raised when an institution feature payload cannot be interpreted safely."""


def _finite_float(payload: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    value = payload.get(key, default)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise FeatureValidationError(f"{key} must be numeric") from exc
    if not np.isfinite(number):
        raise FeatureValidationError(f"{key} must be finite")
    return number


def extract_features(payload: Mapping[str, Any]) -> np.ndarray:
    """Convert an institution payload into the canonical model feature vector."""
    attendance = _finite_float(payload, "attendance")
    beneficiaries = _finite_float(payload, "beneficiaries")
    inspections = _finite_float(payload, "inspections")
    report_variance = _finite_float(payload, "report_variance")
    capacity = _finite_float(payload, "sanctioned_capacity", 0.0)

    if not 0.0 <= attendance <= 100.0:
        raise FeatureValidationError("attendance must be between 0 and 100")
    if beneficiaries < 0.0:
        raise FeatureValidationError("beneficiaries cannot be negative")
    if inspections < 0.0:
        raise FeatureValidationError("inspections cannot be negative")
    if report_variance < 0.0:
        raise FeatureValidationError("report_variance cannot be negative")

    capacity_utilization = beneficiaries / capacity if capacity > 0 else 0.0

    return np.array(
        [
            attendance,
            beneficiaries,
            inspections,
            min(report_variance, 1.0),
            capacity_utilization,
        ],
        dtype=float,
    )


def reference_matrix(records: Sequence[Mapping[str, Any]]) -> np.ndarray:
    """Build the canonical reference matrix from peer institution records."""
    if not records:
        return np.empty((0, len(FEATURE_NAMES)), dtype=float)

    return np.vstack([extract_features(record) for record in records])


def quality_report(payload: Mapping[str, Any], features: np.ndarray) -> dict[str, Any]:
    """Return a compact, API-safe data quality report."""
    expected = ("attendance", "beneficiaries", "inspections", "report_variance")
    missing = [key for key in expected if key not in payload]
    invalid = not np.isfinite(features).all()

    completeness = (len(expected) - len(missing)) / len(expected)
    quality_score = 0.0 if invalid else round(completeness, 3)

    return {
        "quality_score": quality_score,
        "missing_fields": missing,
        "valid": not invalid,
        "status": "VALID" if not invalid and not missing else "PARTIAL",
    }
