from __future__ import annotations

import argparse

from services.api.app.database import SessionLocal
from services.api.app.models import InstitutionMetricDB
from services.ai.external_context import merge_training_context
from services.ai.enriched_training import train_enriched_xgboost


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train RTIN XGBoost using RTIN confirmed outcomes plus external context."
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="External artifact directory; defaults to %USERPROFILE%/rtin-data/models on Windows.",
    )
    args = parser.parse_args()

    from pathlib import Path
    output_dir = args.output_dir or str(
        Path.home() / "rtin-data" / "models"
    )

    db = SessionLocal()
    try:
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
                f"Need at least 20 confirmed labeled observations; found {len(records)}."
            )

        enriched = merge_training_context(db, records)
    finally:
        db.close()

    labels = [int(record["outcome_label"]) for record in enriched]
    result = train_enriched_xgboost(
        enriched,
        labels,
        output_dir,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
