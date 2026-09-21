"""Model registry and monitoring primitives for INSPECT-AI."""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def fingerprint_records(records: Sequence[Mapping[str, Any]]) -> str:
    canonical = json.dumps(
        [dict(sorted(record.items())) for record in records],
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def profile_features(
    records: Sequence[Mapping[str, Any]],
    feature_names: Sequence[str],
    extractor,
) -> dict[str, Any]:
    matrix = np.vstack([extractor(record) for record in records])
    return {
        name: {
            "mean": round(float(np.mean(matrix[:, idx])), 6),
            "std": round(float(np.std(matrix[:, idx])), 6),
            "p05": round(float(np.percentile(matrix[:, idx], 5)), 6),
            "p50": round(float(np.percentile(matrix[:, idx], 50)), 6),
            "p95": round(float(np.percentile(matrix[:, idx], 95)), 6),
        }
        for idx, name in enumerate(feature_names)
    }


def population_stability_index(
    baseline: Sequence[float],
    current: Sequence[float],
    bins: int = 10,
) -> float:
    if not baseline or not current:
        return 0.0

    base = np.asarray(baseline, dtype=float)
    cur = np.asarray(current, dtype=float)
    edges = np.unique(np.quantile(base, np.linspace(0, 1, bins + 1)))

    if len(edges) < 2:
        return 0.0

    base_counts, _ = np.histogram(base, bins=edges)
    cur_counts, _ = np.histogram(cur, bins=edges)

    base_pct = base_counts / max(1, base_counts.sum())
    cur_pct = cur_counts / max(1, cur_counts.sum())
    eps = 1e-6
    return float(np.sum(
        (cur_pct - base_pct)
        * np.log((cur_pct + eps) / (base_pct + eps))
    ))


def drift_report(
    baseline_records: Sequence[Mapping[str, Any]],
    current_records: Sequence[Mapping[str, Any]],
    feature_names: Sequence[str],
    extractor,
    threshold: float = 0.20,
) -> dict[str, Any]:
    if not baseline_records or not current_records:
        return {
            "status": "INSUFFICIENT_DATA",
            "drift_detected": False,
            "threshold": threshold,
            "features": {},
        }

    baseline = np.vstack([extractor(row) for row in baseline_records])
    current = np.vstack([extractor(row) for row in current_records])

    features: dict[str, Any] = {}
    drift_flags = []
    for idx, name in enumerate(feature_names):
        psi = population_stability_index(
            baseline[:, idx].tolist(),
            current[:, idx].tolist(),
        )
        features[name] = {"psi": round(psi, 6), "drift": psi >= threshold}
        drift_flags.append(psi >= threshold)

    return {
        "status": "OK",
        "drift_detected": any(drift_flags),
        "threshold": threshold,
        "features": features,
    }


def save_model_artifact(
    model: Any,
    metadata: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    import joblib

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    model_name = str(metadata["model_name"])
    version = str(metadata["model_version"])
    stem = f"{model_name}__{version}"
    model_path = root / f"{stem}.joblib"
    metadata_path = root / f"{stem}.json"

    joblib.dump(model, model_path)

    record = {
        **dict(metadata),
        "artifact_path": str(model_path),
        "artifact_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "created_at": utc_now().isoformat(),
    }
    metadata_path.write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return record


def list_model_artifacts(output_dir: str | os.PathLike[str]) -> list[dict[str, Any]]:
    root = Path(output_dir)
    if not root.exists():
        return []

    artifacts = []
    for path in sorted(root.glob("*.json")):
        try:
            artifacts.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue

    return sorted(
        artifacts,
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )


def latest_model_status(output_dir: str | os.PathLike[str]) -> dict[str, Any]:
    artifacts = list_model_artifacts(output_dir)
    if not artifacts:
        return {"status": "NO_REGISTERED_MODEL", "artifacts": []}

    latest = artifacts[0]
    model_path = Path(latest["artifact_path"])
    if not model_path.exists():
        return {
            "status": "ARTIFACT_MISSING",
            "latest": latest,
            "artifacts": artifacts,
        }

    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    integrity = digest == latest.get("artifact_sha256")
    return {
        "status": "READY" if integrity else "INTEGRITY_FAILURE",
        "latest": latest,
        "artifacts": artifacts,
        "integrity_ok": integrity,
    }


def load_model_artifact(
    artifact_path: str | os.PathLike[str],
) -> Any:
    import joblib
    return joblib.load(artifact_path)
