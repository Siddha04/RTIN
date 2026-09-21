"""Optional supervised institutional risk model using XGBoost."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from services.ai.features import FEATURE_NAMES, extract_features
from services.ai.mlops import fingerprint_records, save_model_artifact


def train_xgboost_model(
    records: Sequence[Mapping[str, Any]],
    labels: Sequence[int],
    output_dir: str,
    model_version: str = "1.0.0",
) -> dict[str, Any]:
    if len(records) != len(labels):
        raise ValueError("records and labels must have the same length")
    if len(records) < 20:
        raise ValueError("at least 20 labeled observations are required")
    if len(set(int(value) for value in labels)) < 2:
        raise ValueError("both risk outcome classes are required")

    try:
        from sklearn.metrics import accuracy_score, roc_auc_score
        from sklearn.model_selection import train_test_split
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError(
            "Install services/api/requirements-mlops.txt for XGBoost training"
        ) from exc

    X = np.vstack([extract_features(record) for record in records])
    y = np.asarray(labels, dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.90,
        colsample_bytree=0.90,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=1,
    )
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "train_samples": len(y_train),
        "test_samples": len(y_test),
    }

    metadata = {
        "model_name": "inspect-ai-xgboost-risk",
        "model_version": model_version,
        "feature_names": list(FEATURE_NAMES),
        "dataset_fingerprint": fingerprint_records(records),
        "metrics": metrics,
        "objective": "binary institutional risk outcome",
    }

    return save_model_artifact(model, metadata, output_dir)


def predict_xgboost(
    artifact_path: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    import joblib

    model = joblib.load(artifact_path)
    features = extract_features(payload).reshape(1, -1)
    probability = float(model.predict_proba(features)[0, 1])
    return {
        "risk_probability": round(probability, 4),
        "predicted_risk": int(probability >= 0.5),
        "model_artifact": artifact_path,
    }
