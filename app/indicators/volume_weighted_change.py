import pandas as pd


def volume_weighted_change(df: pd.DataFrame, lookback_days: int) -> pd.Series:
    """
    Compute the rolling average of volume-weighted absolute percent change.

    Args:
        df: DataFrame with 'close' and 'volume' columns.
        lookback_days: Rolling window length (e.g. 20 days).

    Returns:
        pd.Series of rolling average volume-weighted change.
    """
    if not {"close", "volume"}.issubset(df.columns):
        raise ValueError("DataFrame must include 'close' and 'volume' columns")

    percent_change = df["close"].pct_change().abs()
    weighted_change = df["volume"] * percent_change
    return weighted_change.rolling(window=lookback_days, min_periods=1).mean()
