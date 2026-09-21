"""Data-driven institutional anomaly and risk analysis.

Phase 1 replaces the prototype's hard-coded ten-row training set with an
explicit peer-reference contract. The model is trained only on reference data
supplied by the caller. During cold start, a transparent policy fallback is
used instead of fabricating training observations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

import numpy as np
from sklearn.ensemble import IsolationForest

from services.ai.features import (
    FEATURE_NAMES,
    MIN_REFERENCE_ROWS,
    FeatureValidationError,
    extract_features,
    quality_report,
    reference_matrix,
)

MODEL_NAME = "inspect-ai-isolation-forest"
MODEL_VERSION = "2.0.0"
RANDOM_STATE = 42


def _clip01(value: float) -> float:
    return float(max(0.0, min(1.0, value)))


def _robust_deviation_score(features: np.ndarray, reference: np.ndarray) -> float:
    """Estimate peer deviation using median/MAD, robust to small outliers."""
    median = np.median(reference, axis=0)
    mad = np.median(np.abs(reference - median), axis=0)
    fallback_scale = np.std(reference, axis=0)
    scale = np.where(mad > 1e-9, 1.4826 * mad, fallback_scale)
    scale = np.where(scale > 1e-9, scale, 1.0)

    robust_z = np.abs((features - median) / scale)
    return _clip01(float(np.mean(np.minimum(robust_z / 4.0, 1.0))))


def _fit_and_score(
    features: np.ndarray,
    reference: np.ndarray,
) -> tuple[float, bool, dict[str, Any]]:
    if len(reference) < MIN_REFERENCE_ROWS:
        return 0.0, False, {
            "status": "INSUFFICIENT_REFERENCE_DATA",
            "reference_rows": int(len(reference)),
        }

    model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(reference)

    reference_decisions = model.decision_function(reference)
    current_decision = float(model.decision_function(features.reshape(1, -1))[0])

    # Low IsolationForest decision values are more anomalous. Convert the
    # position of the current observation in the peer score distribution into
    # a stable 0..1 anomaly score.
    percentile = float(np.mean(reference_decisions <= current_decision))
    anomaly_score = _clip01((0.50 - percentile) * 2.0)

    return anomaly_score, True, {
        "status": "TRAINED_ON_PEER_COHORT",
        "reference_rows": int(len(reference)),
        "n_estimators": 200,
        "contamination": "auto",
        "decision_function": round(current_decision, 6),
    }


def _policy_guardrail_score(payload: Mapping[str, Any], ghost_score: float) -> float:
    """Transparent cold-start guardrails; not presented as learned ML."""
    attendance = float(payload.get("attendance", 0.0))
    variance = max(0.0, float(payload.get("report_variance", 0.0)))

    attendance_guardrail = max(0.0, min(1.0, (60.0 - attendance) / 60.0))
    variance_guardrail = max(0.0, min(1.0, variance / 0.30))

    return _clip01(
        0.55 * variance_guardrail
        + 0.30 * attendance_guardrail
        + 0.15 * ghost_score
    )


def _risk_band(score: int) -> tuple[str, str, str]:
    if score <= 30:
        return "LOW", "Normal monitoring", "No material deviation detected"
    if score <= 60:
        return (
            "MEDIUM",
            "More frequent inspection",
            "Moderate deviation from peer or reporting baseline",
        )
    return (
        "HIGH",
        "Priority / surprise inspection",
        "Significant statistical or reporting anomaly detected",
    )


def analyze_institution(
    d: Dict[str, Any],
    reference_data: Sequence[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Analyze one institution against a caller-supplied peer cohort.

    reference_data is intentionally explicit. This prevents accidental use
    of hidden or stale synthetic training data and makes the same contract
    usable for batch training later.
    """
    try:
        features = extract_features(d)
    except FeatureValidationError as exc:
        return {
            "anomaly": True,
            "anomaly_score": 1.0,
            "risk_score": 100,
            "risk_band": "HIGH",
            "ghost_beneficiary_score": 0.0,
            "recommendation": "Manual data validation required",
            "reason": f"Invalid AI input: {exc}",
            "factors": [{
                "metric": "Data Quality",
                "severity": "HIGH",
                "detail": str(exc),
            }],
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "model_status": "INVALID_INPUT",
            "feature_names": list(FEATURE_NAMES),
            "feature_vector": [],
            "reference_population_size": 0,
            "data_quality": {"quality_score": 0.0, "valid": False},
        }

    quality = quality_report(d, features)
    reference = reference_matrix(reference_data or [])

    cctv_value = d.get("cctv_headcount")
    expected_present = max(
        0.0,
        float(d.get("beneficiaries", 0.0))
        * float(d.get("attendance", 0.0))
        / 100.0,
    )
    if cctv_value is None or expected_present <= 0:
        ghost_score = 0.0
        ghost_source = "UNAVAILABLE"
    else:
        cctv_headcount = max(0.0, float(cctv_value))
        ghost_delta = max(0.0, expected_present - cctv_headcount)
        ghost_score = _clip01(ghost_delta / expected_present)
        ghost_source = "PROVIDED_CCTV_COUNT"

    anomaly_score, model_available, model_meta = _fit_and_score(
        features,
        reference,
    )

    peer_deviation = (
        _robust_deviation_score(features, reference)
        if model_available
        else 0.0
    )
    guardrail = _policy_guardrail_score(d, ghost_score)

    # Learned statistical signal is separated from transparent guardrails.
    risk_score = int(round(
        50.0 * anomaly_score
        + 25.0 * peer_deviation
        + 15.0 * ghost_score
        + 10.0 * guardrail
    ))

    variance = float(d.get("report_variance", 0.0))
    if variance >= 0.20:
        risk_score = max(risk_score, 61)
    if ghost_score >= 0.45:
        risk_score = max(risk_score, 61)

    score = int(max(0, min(100, risk_score)))
    band, recommendation, reason = _risk_band(score)

    factors: List[Dict[str, Any]] = []
    if model_available and anomaly_score >= 0.50:
        factors.append({
            "metric": "Peer Cohort Anomaly",
            "severity": "HIGH" if anomaly_score >= 0.75 else "MEDIUM",
            "detail": (
                "Isolation Forest identified the institution as an unusual "
                "combination of peer features"
            ),
        })
    if model_available and peer_deviation >= 0.50:
        factors.append({
            "metric": "Peer Deviation",
            "severity": "HIGH" if peer_deviation >= 0.75 else "MEDIUM",
            "detail": "Robust median/MAD analysis shows material deviation from the peer cohort",
        })
    if variance >= 0.20:
        factors.append({
            "metric": "Self-Reporting Variance",
            "severity": "HIGH",
            "detail": f"Reported variance is {variance * 100:.1f}%, above the 20% guardrail",
        })
    elif variance > 0.07:
        factors.append({
            "metric": "Self-Reporting Variance",
            "severity": "MEDIUM",
            "detail": f"Reported variance is {variance * 100:.1f}%",
        })
    if ghost_source == "PROVIDED_CCTV_COUNT" and ghost_score > 0.30:
        factors.append({
            "metric": "CCTV / Attendance Discrepancy",
            "severity": "HIGH" if ghost_score >= 0.50 else "MEDIUM",
            "detail": f"CCTV count differs from expected attendance by {ghost_score * 100:.1f}%",
        })
    if not quality["valid"] or quality["status"] != "VALID":
        factors.append({
            "metric": "Data Quality",
            "severity": "MEDIUM",
            "detail": "One or more required model inputs were missing or incomplete",
        })
    if not factors:
        factors.append({
            "metric": "Operational Stability",
            "severity": "LOW",
            "detail": "No material anomaly signal was detected in the available telemetry",
        })

    return {
        "anomaly": bool(anomaly_score >= 0.50 or ghost_score >= 0.45),
        "anomaly_score": round(anomaly_score, 3),
        "peer_deviation_score": round(peer_deviation, 3),
        "risk_score": score,
        "risk_band": band,
        "ghost_beneficiary_score": round(ghost_score, 3),
        "ghost_source": ghost_source,
        "recommendation": recommendation,
        "reason": reason,
        "factors": factors,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "model_status": model_meta["status"],
        "feature_names": list(FEATURE_NAMES),
        "feature_vector": [round(float(v), 6) for v in features],
        "reference_population_size": model_meta["reference_rows"],
        "model_metadata": model_meta,
        "data_quality": quality,
    }
