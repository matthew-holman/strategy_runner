import pandas as pd


def close_position(df: pd.DataFrame) -> pd.Series:
    """
    Compute the position of the close within the daily range.

    Formula:
        (Close - Low) / (High - Low)

    If High == Low, return 0.5 for that row.

    Returns:
        Series of float values in [0, 1], or 0.5 if High == Low.
    """
    required = {"high", "low", "close"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame must contain columns: {required}")

    high = df["high"]
    low = df["low"]
    close = df["close"]

    range_ = high - low

    # cast to float, decimal input incompatible with float
    close_pos = pd.Series(index=df.index, dtype="float64")

    nonzero_mask = range_ != 0
    result = (close[nonzero_mask] - low[nonzero_mask]) / range_[nonzero_mask]

    # Cast result to float before assignment to avoid dtype warning
    close_pos[nonzero_mask] = result.astype(float)

    close_pos[~nonzero_mask] = 0.5

    return close_pos
