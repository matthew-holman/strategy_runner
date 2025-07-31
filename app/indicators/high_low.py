import pandas as pd


def breakout_high_n(df: pd.DataFrame, lookback_days: int = 10) -> pd.Series:
    """
    Compute the N-day breakout high from the 'High' column.
    """
    if "high" not in df.columns:
        raise ValueError("DataFrame must contain 'high' column from ohlcv_daily")

    return df["high"].rolling(window=lookback_days, min_periods=lookback_days).max()


def breakout_low_n(df: pd.DataFrame, lookback_days: int = 10) -> pd.Series:
    """
    Compute the N-day breakout low from the 'Low' column.
    """
    if "low" not in df.columns:
        raise ValueError("DataFrame must contain 'low' column from ohlcv_daily")

    return df["low"].rolling(window=lookback_days, min_periods=lookback_days).min()
