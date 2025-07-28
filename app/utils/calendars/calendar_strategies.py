from abc import ABC, abstractmethod
from datetime import date, timedelta

import pandas_market_calendars as mcal


class TradingCalendar(ABC):
    @abstractmethod
    def get_nth_previous_trading_day(self, as_of: date, lookback_days: int) -> date:
        """Return the calendar date of the Nth previous trading day before 'as_of'."""
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
