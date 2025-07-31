#!/usr/bin/env python

import sys

from app.tasks.candle_ingestion import daily_candle_fetch
from app.tasks.indicator_computation import compute_daily_indicators_for_all_securities
from app.tasks.sp500_ingestion import daily_sp500_sync
from app.utils.log import Log

# Setup logger with a clear application name
logger = Log.setup(application_name="daily-tasks")


def main():
    Log.info("Starting daily update tasks...")

    try:
        Log.info("Running daily_sp500_sync to check S&P500 constituents...")
        daily_sp500_sync()

        Log.info("Running daily_candle_fetch to pull daily ohlcv data...")
        daily_candle_fetch()

        Log.info("Running indicator computation on pulled daily ohlcv data...")
        compute_daily_indicators_for_all_securities()

    except Exception as e:
        Log.critical(f"Daily tasks failed with exception: {e}")
        sys.exit(1)

    Log.info("All daily tasks completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
