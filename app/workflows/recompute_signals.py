#!/usr/bin/env python

import logging
import sys

from datetime import date

from tasks.generate_signals import (
    generate_historic_signals_for_all_strategies,
)

from app.utils.log_setup import configure_logging
from app.utils.log_wrapper import Log


def main() -> int:
    configure_logging(
        logger_name="recompute-signals", level=logging.INFO, use_utc=False
    )
    Log.info("Starting full signal recomputation...")

    try:
        start_date = date(2025, 1, 1)

        generate_historic_signals_for_all_strategies(start_date)

    except Exception as e:
        Log.critical(f"Indicator recomputation failed: {e}")
        return 1

    Log.info("Indicator recomputation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
