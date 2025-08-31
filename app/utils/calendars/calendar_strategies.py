from abc import ABC, abstractmethod
from datetime import date
from typing import List


class TradingCalendar(ABC):
    @abstractmethod
    def get_nth_previous_trading_day(self, as_of: date, lookback_days: int) -> date:
        """DEPRECATED: use get_nth_trading_day(as_of, -lookback_days)."""
        pass

    @abstractmethod
    def get_trading_days_between(self, start: date, end: date) -> List[date]:
        """Return the list of dates where active trading occurred between 2 input dates"""
        pass

    @abstractmethod
    def get_nth_trading_day(self, as_of: date, offset: int) -> date:
        """
        Return the calendar date of the Nth trading day relative to `as_of`.

        Conventions:
        - offset < 0: Nth previous trading day (strictly before `as_of`)
        - offset > 0: Nth next trading day (strictly after `as_of`)
        - offset == 0: if `as_of` is a trading day (and not excluded), return `as_of`;
                       otherwise return the most recent prior trading day.
        """
        pass
