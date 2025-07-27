#!/usr/bin/env python

import sys

from tasks.candle_ingestion import daily_candle_fetch
from tasks.sp500_ingestion import daily_sp500_sync

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

    except Exception as e:
        Log.critical(f"Daily tasks failed with exception: {e}")
        sys.exit(1)

    Log.info("All daily tasks completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
