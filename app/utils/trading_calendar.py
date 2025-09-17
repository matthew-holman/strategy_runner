from datetime import date
from typing import Dict, List

from utils.calendars import CfeCalendar, NyseCalendar

from app.utils.calendars.calendar_strategies import (
    TradingCalendar,
)


class UnsupportedExchangeError(Exception):
    pass


# Calendar strategy registry
_CALENDAR_REGISTRY: Dict[str, TradingCalendar] = {
    "NYSE": NyseCalendar(),
    "NASDAQGS": NyseCalendar(),  # in pandas_market_calendars NASDAQ calendars are an alias of the NYSE cal
    "NASDAQGM": NyseCalendar(),
    "NASDAQCM": NyseCalendar(),
    "NYSEARCA": NyseCalendar(),
    "CBOE US": CfeCalendar(),
}


def get_nth_trading_day(exchange: str, as_of: date, offset: int) -> date:
    """
    Return the calendar date of the Nth previous trading day from a given date.

    Args:
        exchange: Market identifier, e.g., "NYSE", "NASDAQ_STO"
        as_of: Anchor date (inclusive); typically today.
        offset: < 0: Nth previous trading day (strictly before `as_of`)
        offset: > 0: Nth next trading day (strictly after `as_of`)

    Returns:
        The calendar date that is `lookback_days` trading days before `as_of`.
    """
    calendar = _CALENDAR_REGISTRY.get(exchange.upper())
    if not calendar:
        raise UnsupportedExchangeError(f"Exchange '{exchange}' is not supported yet")

    return calendar.get_nth_trading_day(as_of, offset)


def get_all_trading_days_between(exchange: str, start: date, end: date) -> List[date]:
    calendar = _CALENDAR_REGISTRY.get(exchange.upper())
    if not calendar:
        raise UnsupportedExchangeError(f"Exchange '{exchange}' is not supported yet")

    return calendar.get_trading_days_between(start, end)
