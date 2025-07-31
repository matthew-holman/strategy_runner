import pandas as pd


def avg_volume(df: pd.DataFrame, lookback_days: int = 20) -> pd.Series:
    """
    Compute the average volume over a given lookback window.

    Args:
        df: DataFrame containing a 'Volume' column.
        lookback_days: Number of trading days to average over.

    Returns:
        A Series of average volume values, with NaNs for insufficient history.
    """
    if "volume" not in df.columns:
        raise ValueError("DataFrame must contain 'volume' column from ohlcv_daily")

    return df["volume"].rolling(window=lookback_days, min_periods=lookback_days).mean()
