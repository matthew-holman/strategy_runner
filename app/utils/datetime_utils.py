from datetime import date, timedelta


def is_weekend(d: date) -> bool:
    return d.weekday() > 4


def yesterday_was_a_weekend() -> bool:
    return is_weekend(yesterday())


def today_is_a_weekend() -> bool:
    return is_weekend(date.today())


def yesterday() -> date:
    return date.today() - timedelta(days=1)
