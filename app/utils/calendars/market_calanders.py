from datetime import date, timedelta
from typing import List, Set

import pandas_market_calendars as mcal

from app.utils.calendars.calendar_strategies import TradingCalendar


class MarketCalendarBase(TradingCalendar):
    """
    Generic wrapper over pandas_market_calendars.

    Subclasses must set:
      - index_name: str  (e.g., "NYSE", "CFE", "XSTO")
    Optional:
      - excluded_dates: Set[date]  (e.g., {date(2019, 1, 4)} for the NYSE/Yahoo gap)
    """

    index_name: str = ""  # override in subclass
    excluded_dates: Set[date] = set()  # override in subclass if needed

    def __init__(self):
        if not self.index_name:
            raise ValueError("Subclass must set `index_name`.")
        self.calendar = mcal.get_calendar(self.index_name)

    # -------- helpers --------
    def _collect_trading_days(self, start: date, end: date) -> List[date]:
        schedule = self.calendar.schedule(start_date=start, end_date=end)
        days = [ts.date() for ts in schedule.index]
        # Filter excluded dates once, so all methods stay consistent
        return [d for d in days if d not in self.excluded_dates]

    # -------- public API --------
    def get_trading_days_between(self, start: date, end: date) -> List[date]:
        # Inclusive bounds over exchange sessions
        return self._collect_trading_days(start, end)

    def get_nth_previous_trading_day(self, as_of: date, lookback_days: int) -> date:
        if lookback_days <= 0:
            raise ValueError("lookback_days must be positive")
        return self.get_nth_trading_day(as_of, -lookback_days)

    def get_nth_trading_day(self, as_of: date, offset: int) -> date:
        """
        Return the calendar date of the Nth trading day relative to `as_of`.

        Semantics:
        - offset < 0: Nth previous trading day (strictly before `as_of`)
        - offset > 0: Nth next trading day (strictly after `as_of`)
        - offset == 0: if `as_of` is a trading day (and not excluded) return `as_of`,
                       else return the most recent prior trading day.
        """
        if offset == 0:
            raise ValueError("Offset can't be 0.")

        required_days = abs(offset)
        direction = 1 if offset > 0 else -1
        horizon = max(3, required_days * 3)  # cheap heuristic; we expand if needed

        while True:
            if direction > 0:
                start = as_of
                end = as_of + timedelta(days=horizon)
                days = self._collect_trading_days(start, end)
                after = [d for d in days if d > as_of]
                if len(after) >= required_days:
                    return after[required_days - 1]
            else:
                start = as_of - timedelta(days=horizon)
                end = as_of
                days = self._collect_trading_days(start, end)
                before = [d for d in days if d < as_of]
                if len(before) >= required_days:
                    return before[-required_days]

            # Not enough days collected; expand window and try again
            horizon *= 2


# ---------- Subclasses ----------


class CfeCalendar(MarketCalendarBase):
    index_name = "CFE"


class NyseCalendar(MarketCalendarBase):
    index_name = "NYSE"
    # Treat 2019-01-04 as non-trading to match Yahoo OHLCV coverage
    excluded_dates = {date(2019, 1, 4)}
