import pandas as pd


def range_pct(df: pd.DataFrame, lookback_days: int) -> pd.Series:
    """
    Compute the normalized 20-day price range:
    (rolling_max(close) - rolling_min(close)) / rolling_min(close)

    Args:
        df: DataFrame with 'close' column.
        lookback_days: Rolling window length.

    Returns:
        pd.Series of normalized range percentages.
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must include 'close' column")

    rolling_max = df["close"].rolling(window=lookback_days, min_periods=1).max()
    rolling_min = df["close"].rolling(window=lookback_days, min_periods=1).min()
    return (rolling_max - rolling_min) / rolling_min.replace(0, pd.NA)
