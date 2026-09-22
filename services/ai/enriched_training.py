"""Enriched supervised training using RTIN outcomes plus public context.

Public datasets provide contextual features only. Confirmed RTIN inspection
outcomes remain the supervised target.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from services.ai.external_context import CONTEXT_FEATURE_NAMES
from services.ai.features import FEATURE_NAMES, extract_features
from services.ai.mlops import fingerprint_records, save_model_artifact

ENRICHED_FEATURE_NAMES = tuple(FEATURE_NAMES) + tuple(CONTEXT_FEATURE_NAMES)


class TrainingQualityGateError(ValueError):
    """Raised when an evaluated model misses the configured quality gate."""


def extract_enriched_features(record: Mapping[str, Any]) -> np.ndarray:
    core = extract_features(record)
    context = np.asarray(
        [float(record.get(name, 0.0) or 0.0) for name in CONTEXT_FEATURE_NAMES],
        dtype=float,
    )
    return np.concatenate([core, context])


def _build_xgb_classifier():
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError(
            "Install services/api/requirements-mlops.txt for XGBoost training"
        ) from exc

    return XGBClassifier(
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


def evaluate_enriched_xgboost_cv(
    records: Sequence[Mapping[str, Any]],
    labels: Sequence[int],
    *,
    repeats: int = 3,
) -> dict[str, float | int]:
    """Evaluate with repeated stratified CV before fitting the final artifact."""
    try:
        from sklearn.metrics import accuracy_score, roc_auc_score
        from sklearn.model_selection import RepeatedStratifiedKFold
    except ImportError as exc:
        raise RuntimeError("Install scikit-learn for model evaluation") from exc

    normalized_labels = np.asarray([int(value) for value in labels], dtype=int)
    class_counts = {
        int(label): int(np.sum(normalized_labels == label))
        for label in np.unique(normalized_labels)
    }
    if set(class_counts) != {0, 1}:
        raise ValueError("both binary risk outcome classes 0 and 1 are required")

    min_class_count = min(class_counts.values())
    n_splits = min(5, min_class_count)
    if n_splits < 2:
        raise ValueError("each risk outcome class needs at least 2 observations for CV")

    X = np.vstack([extract_enriched_features(record) for record in records])

    splitter = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=max(1, int(repeats)),
        random_state=42,
    )

    accuracies: list[float] = []
    aucs: list[float] = []
    for train_idx, test_idx in splitter.split(X, normalized_labels):
        model = _build_xgb_classifier()
        model.fit(X[train_idx], normalized_labels[train_idx])
        probabilities = model.predict_proba(X[test_idx])[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        accuracies.append(float(accuracy_score(normalized_labels[test_idx], predictions)))
        # Stratification guarantees both classes in each test fold when n_splits
        # is no greater than the minority-class count.
        aucs.append(float(roc_auc_score(normalized_labels[test_idx], probabilities)))

    return {
        "cv_accuracy": round(float(np.mean(accuracies)), 4),
        "cv_accuracy_std": round(float(np.std(accuracies)), 4),
        "cv_roc_auc": round(float(np.mean(aucs)), 4),
        "cv_splits": int(n_splits),
        "cv_repeats": int(max(1, int(repeats))),
        "cv_folds_evaluated": len(accuracies),
    }


def train_enriched_xgboost(
    records: Sequence[Mapping[str, Any]],
    labels: Sequence[int],
    output_dir: str,
    model_version: str = "2.1.0",
    *,
    min_accuracy: float = 0.90,
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

    cv_metrics = evaluate_enriched_xgboost_cv(records, labels)

    if cv_metrics["cv_accuracy"] < float(min_accuracy):
        raise TrainingQualityGateError(
            "public-context XGBoost quality gate failed: "
            f"CV accuracy={cv_metrics['cv_accuracy']:.4f} < "
            f"required={float(min_accuracy):.4f}"
        )

    X = np.vstack([extract_enriched_features(record) for record in records])
    y = np.asarray(normalized_labels, dtype=int)

    model = _build_xgb_classifier()
    model.fit(X, y)

    metadata = {
        "model_name": "inspect-ai-xgboost-risk-enriched",
        "model_version": model_version,
        "feature_names": list(ENRICHED_FEATURE_NAMES),
        "dataset_fingerprint": fingerprint_records(records),
        "metrics": cv_metrics,
        "quality_gate": {
            "metric": "cv_accuracy",
            "minimum": float(min_accuracy),
            "passed": True,
        },
        "train_samples": len(y),
        "objective": (
            "binary institutional risk outcome with public context; "
            "public context never creates the supervised label"
        ),
    }

    return save_model_artifact(model, metadata, output_dir)
