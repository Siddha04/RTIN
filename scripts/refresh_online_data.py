from __future__ import annotations

import argparse

from services.api.app.database import SessionLocal
from services.ai.online_data import refresh_online_data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh RTIN public online data into the external-data store."
    )
    parser.add_argument(
        "--no-realtime",
        action="store_true",
        help="Skip real-time IMD feeds.",
    )
    parser.add_argument(
        "--no-training-context",
        action="store_true",
        help="Skip configured data.gov.in training-context resources.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = refresh_online_data(
            db,
            realtime=not args.no_realtime,
            training_context=not args.no_training_context,
        )
    finally:
        db.close()

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
