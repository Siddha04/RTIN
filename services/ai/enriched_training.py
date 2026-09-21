"""Enriched supervised training using RTIN history plus public context."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from services.ai.external_context import CONTEXT_FEATURE_NAMES
from services.ai.features import FEATURE_NAMES, extract_features
from services.ai.mlops import fingerprint_records, save_model_artifact

ENRICHED_FEATURE_NAMES = tuple(FEATURE_NAMES) + tuple(CONTEXT_FEATURE_NAMES)


def extract_enriched_features(record: Mapping[str, Any]) -> np.ndarray:
    core = extract_features(record)
    context = np.asarray(
        [float(record.get(name, 0.0) or 0.0) for name in CONTEXT_FEATURE_NAMES],
        dtype=float,
    )
    return np.concatenate([core, context])


def train_enriched_xgboost(
    records: Sequence[Mapping[str, Any]],
    labels: Sequence[int],
    output_dir: str,
    model_version: str = "2.0.0",
) -> dict[str, Any]:
    if len(records) != len(labels):
        raise ValueError("records and labels must have the same length")
    if len(records) < 20:
        raise ValueError("at least 20 labeled observations are required")

    normalized_labels = [int(value) for value in labels]
    counts = {value: normalized_labels.count(value) for value in set(normalized_labels)}
    if set(counts) != {0, 1}:
        raise ValueError("both binary risk outcome classes 0 and 1 are required")
    if min(counts.values()) < 2:
        raise ValueError("each risk outcome class needs at least 2 observations")

    try:
        from sklearn.metrics import accuracy_score, roc_auc_score
        from sklearn.model_selection import train_test_split
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError(
            "Install services/api/requirements-mlops.txt for XGBoost training"
        ) from exc

    X = np.vstack([extract_enriched_features(record) for record in records])
    y = np.asarray(normalized_labels, dtype=int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = XGBClassifier(
        n_estimators=350,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.90,
        colsample_bytree=0.85,
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
        "model_name": "inspect-ai-xgboost-risk-enriched",
        "model_version": model_version,
        "feature_names": list(ENRICHED_FEATURE_NAMES),
        "dataset_fingerprint": fingerprint_records(records),
        "metrics": metrics,
        "objective": "binary institutional risk outcome with public context",
    }

    return save_model_artifact(model, metadata, output_dir)
