from datetime import date

import pandas as pd

from sqlmodel import Session

from app.indicators.atr import atr
from app.indicators.avg_volume import avg_volume
from app.indicators.close_position import close_position
from app.indicators.ema import ema
from app.indicators.high_low import breakout_high_n, breakout_low_n
from app.indicators.macd import macd
from app.indicators.rsi import rsi
from app.indicators.sma import sma
from app.utils.trading_calendar import (
    UnsupportedExchangeError,
    get_nth_previous_trading_day,
)

TRADING_DAYS_REQUIRED = 200
EXCHANGE = "NYSE"  # For now, hardcoded until Security model includes exchange


def compute_all_indicators(
    security_id: int, compute_date: date, session: Session
) -> pd.DataFrame:
    """
    Compute indicators for a given security using OHLCV data from start_date up to as_of.

    Args:
        security_id: Ticker or ID of the security
        compute_date: Date we are computing indicators for
        session: Active DB session

    Returns:
        A DataFrame with measurement_date, security_id, and all computed indicators
    """

    try:
        lookback_date = get_nth_previous_trading_day(
            EXCHANGE, as_of=compute_date, lookback_days=TRADING_DAYS_REQUIRED
        )
    except UnsupportedExchangeError as e:
        raise RuntimeError(
            f"Indicator computation failed for {security_id}: {str(e)}"
        ) from e

    df = _load_ohlcv_df(security_id, lookback_date, compute_date, session)

    if df.empty or len(df) < TRADING_DAYS_REQUIRED:
        # TODO add a proper handling mechanism for this, raise an event, add job to queue etc etc
        raise RuntimeError(
            f"Gaps in data for security with id {security_id} between {lookback_date} and {compute_date}"
        )

    df = df.sort_values("candle_date").reset_index(drop=True)

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

    indicators["avg_vol_20d"] = avg_volume(df, lookback_days=20)

    macd_df = macd(df, short_period=12, long_period=26, signal_period=9)
    indicators["macd"] = macd_df["macd"]
    indicators["macd_signal"] = macd_df["macd_signal"]
    indicators["macd_hist"] = macd_df["macd_hist"]

    indicators["atr_14"] = atr(df, lookback_days=14)

    indicators["close_position"] = close_position(df)

    return indicators.iloc[-1]


def _load_ohlcv_df(
    security_id: int, start_date: date, end_date: date, session: Session
) -> pd.DataFrame:
    from app.handlers.ohlcv_daily import OHLCVDailyHandler

    handler = OHLCVDailyHandler(session)
    rows = handler.get_period_for_security(
        start=start_date, end=end_date, security_id=security_id
    )

    return pd.DataFrame([row.model_dump() for row in rows])
