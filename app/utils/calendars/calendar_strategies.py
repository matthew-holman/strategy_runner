from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import List

import pandas_market_calendars as mcal


class TradingCalendar(ABC):
    @abstractmethod
    def get_nth_previous_trading_day(self, as_of: date, lookback_days: int) -> date:
        """Return the calendar date of the Nth previous trading day before 'as_of'."""
        pass

    @abstractmethod
    def get_trading_days_between(self, start: date, end: date) -> List[date]:
        """Return the list of dates where active trading occurred between 2 input dates"""
        pass


class NyseCalendar(TradingCalendar):
    def __init__(self):
        self.calendar = mcal.get_calendar("NYSE")

    def get_nth_previous_trading_day(self, as_of: date, lookback_days: int) -> date:
        schedule = self.calendar.schedule(
            start_date=as_of - timedelta(days=lookback_days * 2), end_date=as_of
        )
        trading_days = schedule.index
        if len(trading_days) < lookback_days:
            raise ValueError(
                f"Only {len(trading_days)} NYSE trading days available before {as_of}"
            )
        return trading_days[-lookback_days].date()

    def get_trading_days_between(self, start: date, end: date) -> List[date]:
        schedule = self.calendar.schedule(start, end).loc[slice(str(start), str(end))]
        return [d.date() for d in schedule.index]


class CfeCalendar(TradingCalendar):
    def __init__(self):
        self.calendar = mcal.get_calendar("CFE")

    def get_nth_previous_trading_day(self, as_of: date, lookback_days: int) -> date:
        schedule = self.calendar.schedule(
            start_date=as_of - timedelta(days=lookback_days * 2), end_date=as_of
        )
        trading_days = schedule.index
        if len(trading_days) < lookback_days:
            raise ValueError(
                f"Only {len(trading_days)} CFE trading days available before {as_of}"
            )
        return trading_days[-lookback_days].date()

    def get_trading_days_between(self, start: date, end: date) -> List[date]:
        schedule = self.calendar.schedule(start, end).loc[slice(str(start), str(end))]
        return [d.date() for d in schedule.index]
