from datetime import date, timedelta
from typing import Iterator


def is_weekend(d: date) -> bool:
    return d.weekday() > 4


def yesterday_was_a_weekend() -> bool:
    return is_weekend(yesterday())


def today_is_a_weekend() -> bool:
    return is_weekend(date.today())


def yesterday() -> date:
    return date.today() - timedelta(days=1)


def chunk_date_range(
    start: date, end: date, chunk_size: timedelta
) -> Iterator[tuple[date, date]]:
    """
    Yield (chunk_start, chunk_end) tuples covering [start, end].

    - If chunk_size is an int, it's interpreted as days.
    - Each chunk_end is inclusive of the range upper bound.
    """
    if start == end:
        yield start, end
        return

    cursor = start
    while cursor < end:
        chunk_end = min(cursor + chunk_size, end)
        yield cursor, chunk_end
        cursor = chunk_end
