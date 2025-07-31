import pandas as pd


def sma(df: pd.DataFrame, lookback_days: int) -> pd.Series:
    """
    Compute the Simple Moving Average (SMA) over a specified lookback window.

    Args:
        df: DataFrame containing at least a 'adjusted_close' column.
        lookback_days: Number of trailing trading days to average over.

    Returns:
        A pd.Series of SMA values aligned with df.index.
        NaN for rows with insufficient lookback.
    """
    if "adjusted_close" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'adjusted_close' column from ohlcv_daily"
        )

    return (
        df["adjusted_close"]
        .rolling(window=lookback_days, min_periods=lookback_days)
        .mean()
    )
