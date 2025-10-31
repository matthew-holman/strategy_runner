import pandas as pd


def price_volume_corr(df: pd.DataFrame, lookback_days: int) -> pd.Series:
    """
    Compute rolling correlation between daily percent change and volume.

    Args:
        df: DataFrame with 'close' and 'volume' columns.
        lookback_days: Rolling window length (e.g. 20 days).

    Returns:
        pd.Series of correlation coefficients.
    """
    if not {"close", "volume"}.issubset(df.columns):
        raise ValueError("DataFrame must include 'close' and 'volume' columns")

    percent_change = df["close"].pct_change()
    return percent_change.rolling(window=lookback_days).corr(df["volume"])
