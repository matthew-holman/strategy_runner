from datetime import date

import pandas as pd

from sqlmodel import Session

from app.indicators.atr import atr
from app.indicators.avg_volume import avg_volume
from app.indicators.breakout_proximity import breakout_proximity
from app.indicators.close_position import close_position
from app.indicators.ema import ema
from app.indicators.exceptions import InsufficientOHLCVDataError
from app.indicators.high_low import breakout_high_n, breakout_low_n
from app.indicators.macd import macd
from app.indicators.percent_change import percent_change
from app.indicators.price_volume_corr import price_volume_corr
from app.indicators.range_pct import range_pct
from app.indicators.rolling_volatility import rolling_volatility
from app.indicators.rsi import rsi
from app.indicators.sma import sma
from app.indicators.volume_weighted_change import volume_weighted_change
from app.utils.trading_calendar import (
    UnsupportedExchangeError,
    get_nth_trading_day,
)

TRADING_DAYS_REQUIRED = 200
EXCHANGE = "NYSE"  # For now, hardcoded until Security model includes exchange


def compute_indicators_for_range(
    security_id: int, start_date: date, end_date: date, session: Session
) -> pd.DataFrame:
    """
    Compute indicators for a given security using OHLCV data from start_date up to as_of.

    Args:
        security_id: Ticker or ID of the security
        start_date: Date we are computing indicators for
        session: Active DB session

    Returns:
        A DataFrame with measurement_date, security_id, and all computed indicators
        :param session:
        :param start_date:
        :param security_id:
        :param end_date:
    """

    try:
        lookback_start = get_nth_trading_day(
            exchange=EXCHANGE, as_of=start_date, offset=-abs(TRADING_DAYS_REQUIRED)
        )
    except UnsupportedExchangeError as e:
        raise RuntimeError(
            f"Indicator computation failed for {security_id}: {str(e)}"
        ) from e

    df = _load_ohlcv_df(security_id, lookback_start, end_date, session)
    if df.empty or "candle_date" not in df.columns:
        raise InsufficientOHLCVDataError(
            security_id=security_id,
            start_date=lookback_start,
            end_date=end_date,
        )

    df = df.sort_values("candle_date").reset_index(drop=True)

    # Normalize numeric types to float64 for compatibility with pandas math
    numeric_columns = ["open", "high", "low", "close", "adjusted_close", "volume"]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("float64")

    if df.empty or len(df) < TRADING_DAYS_REQUIRED:
        raise InsufficientOHLCVDataError(
            security_id=security_id,
            start_date=lookback_start,
            end_date=end_date,
        )

    indicators = pd.DataFrame()
    indicators["measurement_date"] = df["candle_date"]
    indicators["security_id"] = security_id

    indicators["sma_20"] = sma(df, lookback_days=20)
    indicators["sma_50"] = sma(df, lookback_days=50)
    indicators["sma_200"] = sma(df, lookback_days=200)

    indicators["ema_9"] = ema(df, lookback_days=9)
    indicators["ema_20"] = ema(df, lookback_days=20)

    indicators["rsi_14"] = rsi(df, lookback_days=14)

    indicators["high_10d"] = breakout_high_n(df, lookback_days=10)
    indicators["low_10d"] = breakout_low_n(df, lookback_days=10)

    indicators["avg_vol_5d"] = avg_volume(df, lookback_days=5)
    indicators["avg_vol_20d"] = avg_volume(df, lookback_days=20)
    indicators["avg_vol_50d"] = avg_volume(df, lookback_days=50)

    indicators["avg_vol_weighted_change_5d"] = volume_weighted_change(
        df, lookback_days=5
    )
    indicators["avg_vol_weighted_change_50d"] = volume_weighted_change(
        df, lookback_days=50
    )

    indicators["price_volume_corr_20"] = price_volume_corr(df, lookback_days=20)

    macd_df = macd(df, short_period=12, long_period=26, signal_period=9)
    indicators["macd"] = macd_df["macd"]
    indicators["macd_signal"] = macd_df["macd_signal"]
    indicators["macd_hist"] = macd_df["macd_hist"]

    indicators["atr_14"] = atr(df, lookback_days=14)

    indicators["close_position"] = close_position(df)
    indicators["percent_change"] = percent_change(df)

    indicators["range_pct_20"] = range_pct(df, lookback_days=20)
    indicators["breakout_proximity_20"] = breakout_proximity(df, lookback_days=20)
    indicators["rolling_volatility_20"] = rolling_volatility(df, lookback_days=20)

    # Return only the rows between start_date and end_date
    return indicators[
        (indicators["measurement_date"] >= start_date)
        & (indicators["measurement_date"] <= end_date)
    ]


def _load_ohlcv_df(
    security_id: int, start_date: date, end_date: date, session: Session
) -> pd.DataFrame:
    from app.handlers.ohlcv_daily import OHLCVDailyHandler

    handler = OHLCVDailyHandler(session)
    rows = handler.get_period_for_security(
        start=start_date, end=end_date, security_id=security_id
    )

    return pd.DataFrame([row.model_dump() for row in rows])
