from datetime import date
from typing import Dict

from app.utils.calendars.calendar_strategies import NyseCalendar, TradingCalendar


class UnsupportedExchangeError(Exception):
    pass


# Calendar strategy registry
_CALENDAR_REGISTRY: Dict[str, TradingCalendar] = {
    "NYSE": NyseCalendar(),
    # "NASDAQ_STO": Not yet implemented
}


def get_nth_previous_trading_day(
    exchange: str, as_of: date, lookback_days: int
) -> date:
    """
    Return the calendar date of the Nth previous trading day from a given date.

    Args:
        exchange: Market identifier, e.g., "NYSE", "NASDAQ_STO"
        as_of: Anchor date (inclusive); typically today.
        lookback_days: Number of trading days to look back.

    Returns:
        The calendar date that is `lookback_days` trading days before `as_of`.
    """
    calendar = _CALENDAR_REGISTRY.get(exchange.upper())
    if not calendar:
        raise UnsupportedExchangeError(f"Exchange '{exchange}' is not supported yet")

    return calendar.get_nth_previous_trading_day(as_of, lookback_days)
