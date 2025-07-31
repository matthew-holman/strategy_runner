import pandas as pd


def macd(
    df: pd.DataFrame,
    short_period: int = 12,
    long_period: int = 26,
    signal_period: int = 9,
) -> pd.DataFrame:
    """
    Compute MACD, signal line, and histogram for a given DataFrame of adjusted_close prices.

    Returns:
        DataFrame with columns: 'macd', 'macd_signal', 'macd_hist'
    """
    if "adjusted_close" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'adjusted_close' column from ohlcv_daily"
        )

    short_ema = df["adjusted_close"].ewm(span=short_period, adjust=False).mean()
    long_ema = df["adjusted_close"].ewm(span=long_period, adjust=False).mean()
    macd_line = short_ema - long_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame(
        {"macd": macd_line, "macd_signal": signal_line, "macd_hist": histogram}
    )
