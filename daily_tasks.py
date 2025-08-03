#!/usr/bin/env python

import sys

from tasks.update_securities import check_for_missing_metadata

from app.tasks.candle_ingestion import daily_candle_fetch, heal_missing_candle_data
from app.tasks.indicator_computation import (
    compute_daily_indicators_for_all_securities,
    heal_missing_technical_indicators,
)
from app.tasks.sp500_ingestion import daily_sp500_sync
from app.utils.log import Log

# Setup logger with a clear application name
logger = Log.setup(application_name="daily-tasks")


def main():
    Log.info("Starting daily update tasks...")

    try:
        Log.info("Running daily_sp500_sync to check S&P500 constituents...")
        daily_sp500_sync()

        Log.info("Running security metadata update.")
        check_for_missing_metadata()

        Log.info("Running daily_candle_fetch to pull daily ohlcv data...")
        daily_candle_fetch()

        Log.info("Running historical backfill to fill gaps in the ohlcv data.")
        heal_missing_candle_data()

        Log.info("Running indicator computation on pulled daily ohlcv data...")
        compute_daily_indicators_for_all_securities()

        Log.info("Running historical backfill to fill gaps in the computed indicators.")
        heal_missing_technical_indicators()

    except Exception as e:
        Log.critical(f"Daily tasks failed with exception: {e}")
        sys.exit(1)

    Log.info("All daily tasks completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
