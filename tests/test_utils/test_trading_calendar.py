from datetime import date

import pytest

from freezegun import freeze_time

from app.utils.trading_calendar import (
    UnsupportedExchangeError,
    get_nth_previous_trading_day,
)


def test_get_nth_previous_trading_day_nyse():
    today = date.today()
    lookback = 20

    result = get_nth_previous_trading_day("NYSE", as_of=today, lookback_days=lookback)

    assert isinstance(result, date)
    assert result < today
    # Should be approximately `lookback` weekdays ago — test loosely
    assert (today - result).days >= lookback
    assert (today - result).days <= lookback * 2


@freeze_time("2024-12-31")
def test_get_200th_previous_trading_day_nyse():
    # This expected date is based on NYSE calendar (known 200th trading day before 2024-12-31)
    expected_date = date(2024, 3, 15)
    result = get_nth_previous_trading_day("NYSE", as_of=date.today(), lookback_days=200)

    assert result == expected_date


def test_get_nth_previous_trading_day_invalid_exchange():
    with pytest.raises(UnsupportedExchangeError) as exc_info:
        get_nth_previous_trading_day("MOONDEX", as_of=date.today(), lookback_days=10)

    assert "not supported" in str(exc_info.value).lower()
