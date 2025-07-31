import pandas as pd


def rsi(df: pd.DataFrame, lookback_days: int = 14) -> pd.Series:
    """
    Compute the Relative Strength Index (RSI) over a given lookback window.

    Args:
        df: DataFrame containing a 'adjusted_close' column.
        lookback_days: Number of trailing days to use in RSI calculation.

    Returns:
        A pd.Series of RSI values (0–100), same length as input, with NaNs during warm-up.
    """
    if "adjusted_close" not in df.columns:
        raise ValueError("DataFrame must contain 'adjusted_close' column.")

    delta = df["adjusted_close"].diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / lookback_days, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / lookback_days, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
