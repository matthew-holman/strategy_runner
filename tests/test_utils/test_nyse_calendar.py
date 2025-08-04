from datetime import date

from app.utils.calendars.calendar_strategies import NyseCalendar


def test_trading_days_between_removes_jan_4_2019():
    calendar = NyseCalendar()
    start = date(2019, 1, 1)
    end = date(2019, 1, 10)

    trading_days = calendar.get_trading_days_between(start, end)

    assert date(2019, 1, 4) not in trading_days, "Jan 4, 2019 should have been removed"
    assert date(2019, 1, 3) in trading_days
    assert date(2019, 1, 7) in trading_days
    assert all(isinstance(d, date) for d in trading_days)


def test_nth_previous_trading_day_skips_jan_4_2019():
    calendar = NyseCalendar()
    as_of = date(2019, 1, 7)

    # Without the override, 4th previous day would have been Jan 4
    # But we expect Jan 3 instead due to the skip
    nth_day = calendar.get_nth_previous_trading_day(as_of=as_of, lookback_days=4)

    # the result should be the 1st but due to ignoring the 4th of Jan
    # it pushes the date back 1 day.
    assert nth_day == date(2018, 12, 31)
