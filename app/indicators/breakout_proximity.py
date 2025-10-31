import pandas as pd


def breakout_proximity(df: pd.DataFrame, lookback_days: int) -> pd.Series:
    """
    Compute how close the current close is to the rolling max (resistance):
    (close / rolling_max(close)) - 1

    Args:
        df: DataFrame with 'close' column.
        lookback_days: Rolling window length.

    Returns:
        pd.Series of proximity ratios (0 means at resistance, -0.05 means 5% below).
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must include 'close' column")

    rolling_max = df["close"].rolling(window=lookback_days, min_periods=1).max()
    return (df["close"] / rolling_max) - 1
