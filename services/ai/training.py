"""Training orchestration for reproducible INSPECT-AI models."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.ensemble import IsolationForest

from services.ai.features import FEATURE_NAMES, extract_features
from services.ai.mlops import (
    fingerprint_records,
    profile_features,
    save_model_artifact,
)
from services.ai.supervised import train_xgboost_model


def train_isolation_forest_model(
    records: Sequence[Mapping[str, Any]],
    output_dir: str,
    model_version: str = "2.1.0",
) -> dict[str, Any]:
    if len(records) < 8:
        raise ValueError("at least 8 observations are required")

    matrix = np.vstack([extract_features(record) for record in records])
    model = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=42,
        n_jobs=1,
    )
    model.fit(matrix)

    decisions = model.decision_function(matrix)
    metadata = {
        "model_name": "inspect-ai-isolation-forest",
        "model_version": model_version,
        "feature_names": list(FEATURE_NAMES),
        "dataset_fingerprint": fingerprint_records(records),
        "samples": len(records),
        "training_statistics": {
            "decision_mean": round(float(np.mean(decisions)), 6),
            "decision_std": round(float(np.std(decisions)), 6),
        },
        "feature_profile": profile_features(records, FEATURE_NAMES, extract_features),
    }
    return save_model_artifact(model, metadata, output_dir)


def train_from_records(
    records: Sequence[Mapping[str, Any]],
    output_dir: str,
    model_type: str,
) -> dict[str, Any]:
    normalized = model_type.strip().lower()
    if normalized in {"isolation_forest", "isolation-forest"}:
        return train_isolation_forest_model(records, output_dir)

    if normalized == "xgboost":
        labels = [
            int(record["outcome_label"])
            for record in records
            if record.get("outcome_label") is not None
        ]
        labeled = [
            record for record in records
            if record.get("outcome_label") is not None
        ]
        return train_xgboost_model(labeled, labels, output_dir)

    raise ValueError(f"unsupported model_type: {model_type}")
