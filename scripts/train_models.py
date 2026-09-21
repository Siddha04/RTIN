from __future__ import annotations

import argparse

from services.api.app.database import SessionLocal
from services.api.app.models import InstitutionMetricDB
from services.ai.training import train_from_records


def main() -> int:
    parser = argparse.ArgumentParser(description="Train INSPECT-AI models")
    parser.add_argument(
        "--model",
        choices=["isolation_forest", "xgboost"],
        default="isolation_forest",
    )
    parser.add_argument(
        "--output-dir",
        default="services/api/artifacts/models",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        rows = db.query(InstitutionMetricDB).order_by(
            InstitutionMetricDB.recorded_at.asc()
        ).all()
        records = [
            {
                "attendance": row.attendance,
                "beneficiaries": row.beneficiaries,
                "inspections": row.inspections,
                "report_variance": row.report_variance,
                "sanctioned_capacity": row.sanctioned_capacity,
                "outcome_label": row.outcome_label,
            }
            for row in rows
        ]
    finally:
        db.close()

    result = train_from_records(records, args.output_dir, args.model)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
