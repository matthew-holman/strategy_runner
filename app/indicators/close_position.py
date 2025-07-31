import pandas as pd


def close_position(df: pd.DataFrame) -> pd.Series:
    """
    Compute the position of the close within the daily range.

    Formula:
        (Close - Low) / (High - Low)

    Returns:
        Series of values in [0, 1], or 0.5 if High == Low.
    """
    required = {"high", "low", "close"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame must contain columns: {required}")

    high = df["high"]
    low = df["low"]
    close = df["close"]

    range_ = high - low
    close_pos = (close - low) / range_

    # Handle divide-by-zero (High == Low) → return 0.5
    return close_pos.fillna(0.5)
