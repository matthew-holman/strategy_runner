from datetime import date

import pytest

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


def test_get_nth_previous_trading_day_invalid_exchange():
    with pytest.raises(UnsupportedExchangeError) as exc_info:
        get_nth_previous_trading_day("MOONDEX", as_of=date.today(), lookback_days=10)

    assert "not supported" in str(exc_info.value).lower()
