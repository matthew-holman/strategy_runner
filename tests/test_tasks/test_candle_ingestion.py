import pytest

from tasks.candle_ingestion import daily_candle_fetch, historical_candle_backfill


@pytest.mark.skip(reason="Debug entry point only")
def test_daily_candle_fetch_debug():
    # This will hit yahoo finance api and try to insert into the DB
    daily_candle_fetch()

    # Optional: assert on side effects if desired
    # e.g., check logs, DB rows, etc.


# @pytest.mark.skip(reason="Debug entry point only")
def test_historic_candle_fetch_debug():
    # This will hit yahoo finance api and try to insert into the DB
    historical_candle_backfill()

    # Optional: assert on side effects if desired
    # e.g., check logs, DB rows, etc.
