#!/usr/bin/env python

import logging
import sys

from app.tasks.candle_ingestion import daily_candle_fetch, heal_missing_candle_data
from app.tasks.generate_signals import generate_daily_signals
from app.tasks.indicator_computation import (
    compute_daily_indicators_for_all_securities,
    heal_missing_technical_indicators,
)
from app.tasks.ticker_ingestion import region_security_sync
from app.tasks.update_securities import check_for_missing_metadata
from app.utils.datetime_utils import yesterday_was_a_weekend
from app.utils.log_setup import configure_logging
from app.utils.log_wrapper import Log


def main() -> int:
    configure_logging(logger_name="eod-tasks", level=logging.INFO, use_utc=False)

    Log.info("Starting end of day tasks...")
    try:
        if yesterday_was_a_weekend():
            Log.info("Yesterday was a weekend; no data to pull.")
            return 0

        Log.info("Updating tickers, checking for the largest 3000 securities.")
        new_tickers_added = region_security_sync()

        if new_tickers_added:
            Log.info("Updating security metadata.")
            check_for_missing_metadata()
        else:
            Log.info("No ticker changes; skipping metadata fetch.")

        Log.info("Fetching daily OHLCV data...")
        daily_candle_fetch()

        if new_tickers_added:
            Log.info("Healing OHLCV gaps (historical backfill).")
            heal_missing_candle_data()
        else:
            Log.info("No ticker changes; skipping OHLCV backfill.")

        Log.info("Computing indicators on pulled daily OHLCV data...")
        compute_daily_indicators_for_all_securities()

        if new_tickers_added:
            Log.info("Healing indicator gaps (historical backfill).")
            heal_missing_technical_indicators()
        else:
            Log.info("No ticker changes; skipping indicator backfill.")

        Log.info("Generating daily signals...")
        generate_daily_signals()

    except Exception as e:
        Log.critical(f"EOD tasks failed with exception: {e}")
        return 1

    Log.info("All end of day tasks completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
