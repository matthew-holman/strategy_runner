import numpy as np
import pandas as pd


def avg_volume(df: pd.DataFrame, lookback_days: int = 20) -> pd.Series:
    """
    Compute the average volume over a given lookback window.
    Any window that includes a zero-volume day will return NaN.

    Args:
        df: DataFrame containing a 'volume' column.
        lookback_days: Number of trading days to average over.

    Returns:
        A Series of average volume values, with NaNs for insufficient history or zero-volume days.
    """
    if "volume" not in df.columns:
        raise ValueError("DataFrame must contain 'volume' column from ohlcv_daily")

    # Mark zero-volume entries as NaN
    safe_volume = df["volume"].copy()

    # If any zero in the rolling window, result is NaN
    def zero_sensitive_avg(window):
        return np.nan if (window == 0).any() else window.mean()

    return safe_volume.rolling(window=lookback_days, min_periods=lookback_days).apply(
        zero_sensitive_avg, raw=True
    )
