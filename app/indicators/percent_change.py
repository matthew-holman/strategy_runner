import pandas as pd


def percent_change(df: pd.DataFrame) -> pd.Series:
    """
    Compute the daily percent change in close price.

    Args:
        df: DataFrame with a 'close' column, ordered by date ascending.

    Returns:
        pd.Series containing percent change values (NaN for the first row).
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must include a 'close' column")

    return df["close"].pct_change()
