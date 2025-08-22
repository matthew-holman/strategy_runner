# tests/tasks/test_sp500_ingestion.py
import pytest

from app.tasks.sp500_ingestion import backfill_sp500_from_wayback, daily_sp500_sync


@pytest.mark.skip(reason="Debug entry point only")
def test_daily_sp500_sync_debug():
    # This will hit Wikipedia and try to insert into your DB
    daily_sp500_sync()

    # Optional: assert on side effects if desired
    # e.g., check logs, DB rows, etc.


@pytest.mark.skip(reason="Debug entry point only")
def test_backfill_sp500_from_wayback():
    # This will hit Wikipedia and try to insert into your DB
    backfill_sp500_from_wayback()

    # Optional: assert on side effects if desired
    # e.g., check logs, DB rows, etc.
