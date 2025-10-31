#!/usr/bin/env python

import logging
import sys

from datetime import date

from app.tasks.indicator_computation import recompute_indicators_for_all_securities
from app.utils.log_setup import configure_logging
from app.utils.log_wrapper import Log


def main() -> int:
    configure_logging(
        logger_name="recompute-indicators", level=logging.INFO, use_utc=False
    )
    Log.info("Starting full indicator recomputation...")

    try:
        start_date = date(2025, 1, 1)
        end_date = date.today()

        recompute_indicators_for_all_securities(start_date, end_date)

    except Exception as e:
        Log.critical(f"Indicator recomputation failed: {e}")
        return 1

    Log.info("Indicator recomputation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
