# tests/tasks/test_daily_sp500_sync.py


from tasks.sp500_ingestion import daily_sp500_sync


# @pytest.mark.skip(reason="Debug entry point only")
def test_daily_sp500_sync_debug():
    # This will hit Wikipedia and try to insert into your DB
    daily_sp500_sync()

    # Optional: assert on side effects if desired
    # e.g., check logs, DB rows, etc.
