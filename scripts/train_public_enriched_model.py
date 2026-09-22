from __future__ import annotations

import argparse
from pathlib import Path

from services.api.app.database import SessionLocal
from services.api.app.models import InstitutionMetricDB
from services.ai.enriched_training import train_enriched_xgboost
from services.ai.external_context import merge_training_context
from services.ai.online_data import refresh_online_data


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh configured public data, join it to RTIN confirmed outcomes, "
            "and train the enriched XGBoost model."
        )
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="External artifact directory; defaults to ~/rtin-data/models.",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=0.90,
        help="Minimum repeated-CV accuracy required to register the model.",
    )
    parser.add_argument(
        "--skip-refresh",
        action="store_true",
        help="Train from already-ingested public observations.",
    )
    args = parser.parse_args()

    if not 0.0 <= args.min_accuracy <= 1.0:
        raise SystemExit("--min-accuracy must be between 0 and 1")

    output_dir = args.output_dir or str(Path.home() / "rtin-data" / "models")

    db = SessionLocal()
    try:
        if not args.skip_refresh:
            refresh_result = refresh_online_data(
                db,
                realtime=True,
                training_context=True,
            )
            print({"online_refresh": refresh_result})

        rows = db.query(InstitutionMetricDB).filter(
            InstitutionMetricDB.outcome_label.in_([0, 1])
        ).order_by(InstitutionMetricDB.recorded_at.asc()).all()

        records = [
            {
                "district": row.district,
                "attendance": row.attendance,
                "beneficiaries": row.beneficiaries,
                "inspections": row.inspections,
                "report_variance": row.report_variance,
                "sanctioned_capacity": row.sanctioned_capacity,
                "outcome_label": row.outcome_label,
            }
            for row in rows
        ]

        if len(records) < 20:
            raise SystemExit(
                "Need at least 20 confirmed RTIN inspection outcomes; "
                f"found {len(records)}."
            )

        enriched = merge_training_context(db, records)
    finally:
        db.close()

    labels = [int(record["outcome_label"]) for record in enriched]
    result = train_enriched_xgboost(
        enriched,
        labels,
        output_dir,
        model_version="2.1.0",
        min_accuracy=args.min_accuracy,
    )

    print({
        "status": "TRAINING_GATE_PASSED",
        "cv_accuracy": result["metrics"]["cv_accuracy"],
        "cv_accuracy_std": result["metrics"]["cv_accuracy_std"],
        "cv_roc_auc": result["metrics"]["cv_roc_auc"],
        "artifact_path": result["artifact_path"],
        "artifact_sha256": result["artifact_sha256"],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
