import pandas as pd


def ema(df: pd.DataFrame, lookback_days: int) -> pd.Series:
    """
    Compute the Exponential Moving Average (EMA) over a given lookback window.

    Args:
        df: DataFrame containing at least a 'adjusted_close' column.
        lookback_days: Number of days to use for the EMA.

    Returns:
        A Series of EMA values, same length as df, with NaN for the warm-up period.
    """
    if "adjusted_close" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'adjusted_close' column from ohlcv_daily"
        )

    return df["adjusted_close"].ewm(span=lookback_days, adjust=False).mean()
