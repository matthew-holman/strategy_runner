import pandas as pd


def atr(df: pd.DataFrame, lookback_days: int = 14) -> pd.Series:
    """
    Compute Average True Range (ATR) using EMA over a given lookback period.

    Args:
        df: DataFrame with columns ['high', 'low', 'close']
        lookback_days: Number of trading days to average over

    Returns:
        Series of ATR values (NaN for insufficient data)
    """
    required = {"high", "low", "close"}
    if not required.issubset(df.columns):
        raise ValueError(f"DataFrame must contain: {required}")

    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)

    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)

    atr_result = tr.ewm(alpha=1 / lookback_days, adjust=False).mean()
    return atr_result
