import pytest

from app.tasks.candle_ingestion import daily_candle_fetch


@pytest.mark.skip(reason="Debug entry point only")
def test_daily_candle_fetch_debug():
    # This will hit yahoo finance api and try to insert into the DB
    daily_candle_fetch()

    # Optional: assert on side effects if desired
    # e.g., check logs, DB rows, etc.
