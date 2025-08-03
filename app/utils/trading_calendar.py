from datetime import date
from typing import Dict, List

from app.utils.calendars.calendar_strategies import (
    CfeCalendar,
    NyseCalendar,
    TradingCalendar,
)


class UnsupportedExchangeError(Exception):
    pass


# Calendar strategy registry
_CALENDAR_REGISTRY: Dict[str, TradingCalendar] = {
    "NYSE": NyseCalendar(),
    "NASDAQGS": NyseCalendar(),  # in pandas_market_calendars NASDAQ calendars are a alias of the NYSE cal
    "NASDAQGM": NyseCalendar(),
    "NASDAQCM": NyseCalendar(),
    "NYSEARCA": NyseCalendar(),
    "CBOE US": CfeCalendar(),
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

    lookback_adjusted = (
        lookback_days + 1
    )  # we need to pad by a day to get correct result
    return calendar.get_nth_previous_trading_day(as_of, lookback_adjusted)


def get_all_trading_days_between(exchange: str, start: date, end: date) -> List[date]:
    calendar = _CALENDAR_REGISTRY.get(exchange.upper())
    if not calendar:
        raise UnsupportedExchangeError(f"Exchange '{exchange}' is not supported yet")

    return calendar.get_trading_days_between(start, end)
