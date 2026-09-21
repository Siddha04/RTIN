from typing import Any, Dict, List
import numpy as np
from sklearn.ensemble import IsolationForest

# IsolationForest model trained on typical institution baseline features:
# [attendance_rate, beneficiaries, inspections_count, report_variance, ghost_headcount_ratio]
TRAINING_DATA = np.array([
    [40, 420, 5, 0.03, 0.95],
    [41, 430, 5, 0.04, 0.93],
    [39, 410, 6, 0.02, 0.96],
    [42, 400, 5, 0.05, 0.92],
    [40, 415, 4, 0.03, 0.94],
    [55, 290, 7, 0.10, 0.70],
    [37, 610, 3, 0.08, 0.65],
    [85, 120, 4, 0.02, 0.98],
    [30, 500, 2, 0.15, 0.50],
    [65, 310, 6, 0.06, 0.88],
])

MODEL = IsolationForest(contamination=0.25, random_state=42, n_estimators=150)
MODEL.fit(TRAINING_DATA[:, :4])

def analyze_institution(d: Dict[str, Any]) -> Dict[str, Any]:
    att = float(d.get("attendance", 0))
    bene = float(d.get("beneficiaries", 0))
    insp = float(d.get("inspections", 0))
    var = float(d.get("report_variance", 0))

    # Features for Isolation Forest
    x = np.array([[att, bene, insp, var]], dtype=float)
    pred = int(MODEL.predict(x)[0])
    decision = float(MODEL.decision_function(x)[0])
    anomaly = max(0.0, min(1.0, (0.15 - decision) / 0.45))

    # Ghost Beneficiary & Proxy Staff analysis
    cctv_headcount = float(d.get("cctv_headcount", bene * (att / 100.0) if bene > 0 else 0))
    expected_present = bene * (att / 100.0) if bene > 0 else 0
    ghost_delta = max(0.0, expected_present - cctv_headcount)
    ghost_ratio = (ghost_delta / expected_present) if expected_present > 0 else 0.0
    ghost_score = round(min(1.0, ghost_ratio), 3)

    # Multi-factor score computation (0 - 100)
    base_score = int(round(max(0, min(100,
        25 * anomaly +
        40 * min(abs(att - 41) / 51, 1.0) +
        20 * min(var / 0.30, 1.0) +
        15 * ghost_score
    ))))

    if pred == -1 or ghost_score > 0.45:
        base_score = max(base_score, 61)

    score = min(100, max(0, base_score))

    if score <= 30:
        band = "LOW"
        recommendation = "Normal monitoring"
        reason = "Normal institutional pattern"
    elif score <= 60:
        band = "MEDIUM"
        recommendation = "More frequent inspection"
        reason = "Moderate deviation from historical baseline"
    else:
        band = "HIGH"
        recommendation = "Priority / surprise inspection"
        reason = "Unusual attendance / record pattern detected"

    # Actionable Explainability Factors for DoSJE Officials
    factors: List[Dict[str, Any]] = []
    if ghost_score > 0.30:
        factors.append({
            "metric": "Ghost Beneficiary Discrepancy",
            "severity": "HIGH" if ghost_score > 0.50 else "MEDIUM",
            "detail": f"CCTV crowd estimation indicates potential ghost reporting (variance: {int(ghost_score * 100)}%)"
        })
    if var > 0.07:
        factors.append({
            "metric": "Self-Reporting Variance",
            "severity": "MEDIUM",
            "detail": f"High discrepancy between NGO reported records and field audit samples ({int(var * 100)}%)"
        })
    if abs(att - 41) > 20:
        factors.append({
            "metric": "Attendance Irregularity",
            "severity": "MEDIUM",
            "detail": f"Attendance rate ({att:.1f}%) diverges significantly from state scheme benchmark"
        })
    if pred == -1:
        factors.append({
            "metric": "Machine Learning Anomaly Flag",
            "severity": "HIGH",
            "detail": "Isolation Forest flagged institutional feature combination as a statistical outlier"
        })

    if not factors:
        factors.append({
            "metric": "Operational Stability",
            "severity": "LOW",
            "detail": "All telemetry, attendance logs, and CCTV feeds operate within standard compliance thresholds"
        })

    return {
        "anomaly": pred == -1 or ghost_score > 0.45,
        "anomaly_score": round(anomaly, 3),
        "risk_score": score,
        "risk_band": band,
        "ghost_beneficiary_score": ghost_score,
        "recommendation": recommendation,
        "reason": reason,
        "factors": factors
    }
