import pandas as pd


def rolling_volatility(df: pd.DataFrame, lookback_days: int) -> pd.Series:
    """
    Compute normalized rolling volatility: std(close) / mean(close)

    Args:
        df: DataFrame with 'close' column.
        lookback_days: Rolling window length.

    Returns:
        pd.Series of normalized volatility.
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must include 'close' column")

    rolling_std = df["close"].rolling(window=lookback_days, min_periods=1).std()
    rolling_mean = df["close"].rolling(window=lookback_days, min_periods=1).mean()
    return rolling_std / rolling_mean.replace(0, pd.NA)
