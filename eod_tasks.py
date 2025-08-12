#!/usr/bin/env python

import sys

from app.tasks.candle_ingestion import daily_candle_fetch, heal_missing_candle_data
from app.tasks.generate_signals import generate_daily_signals
from app.tasks.indicator_computation import (
    compute_daily_indicators_for_all_securities,
    heal_missing_technical_indicators,
)
from app.tasks.sp500_ingestion import daily_sp500_sync
from app.tasks.update_securities import check_for_missing_metadata
from app.utils.datetime_utils import yesterday_was_a_weekend
from app.utils.log import Log

# Setup logger with a clear application name
logger = Log.setup(log_name="daily-tasks")


def main():
    Log.info("Starting daily update tasks...")
    try:

        if yesterday_was_a_weekend():
            Log.info("Yesterday was a weekend, no data to pull.")
        else:

            Log.info("Running daily_sp500_sync to check S&P500 constituents...")
            has_sp500_changed = daily_sp500_sync()

            if has_sp500_changed:
                Log.info("Running security metadata update.")
                check_for_missing_metadata()
            else:
                Log.info("No changes to S&P500, skipping metadata fetch")

            Log.info("Running daily_candle_fetch to pull daily ohlcv data...")
            daily_candle_fetch()

            if has_sp500_changed:
                Log.info("Running historical backfill to fill gaps in the ohlcv data.")
                heal_missing_candle_data()
            else:
                Log.info("No changes to S&P500, historic ohlcv fetch")

            Log.info("Running indicator computation on pulled daily ohlcv data...")
            compute_daily_indicators_for_all_securities()

            if has_sp500_changed:
                Log.info(
                    "Running historical backfill to fill gaps in the computed indicators."
                )
                heal_missing_technical_indicators()
            else:
                Log.info("No changes to S&P500, skipping ")

            generate_daily_signals("sma_pullback_buy.json")

    except Exception as e:
        Log.critical(f"Daily tasks failed with exception: {e}")
        sys.exit(1)

    Log.info("All daily tasks completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
