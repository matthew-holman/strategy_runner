from datetime import date
from decimal import InvalidOperation
from typing import Optional

import pandas as pd

from app.core.db import get_db
from app.handlers.security import SecurityHandler
from app.handlers.technical_indicator import TechnicalIndicatorHandler
from app.indicators.compute import compute_indicators_for_range
from app.indicators.exceptions import InsufficientOHLCVDataError
from app.models.technical_indicator import TechnicalIndicator
from app.utils.datetime_utils import last_year, yesterday
from app.utils.log_wrapper import Log
from app.utils.trading_calendar import (
    get_all_trading_days_between,
)


def compute_daily_indicators_for_all_securities(
    compute_date: date = yesterday(),
) -> None:
    """
    Task: Compute and persist technical indicators for each security for a given date.

    Args:
        compute_date: The date to compute indicators for (default: today).
    """
    Log.info(f"Running indicator update for {compute_date}")

    with next(get_db()) as db_session:
        technical_indicator_handler = TechnicalIndicatorHandler(db_session)
        security_handler = SecurityHandler(db_session)
        all_securities = security_handler.get_all()

        for security in all_securities:
            try:
                try:
                    df = compute_indicators_for_range(
                        security_id=security.id,
                        start_date=compute_date,
                        end_date=compute_date,
                        session=db_session,
                    )
                except InsufficientOHLCVDataError as e:
                    Log.warning(
                        f"Insufficient OHLCV data for indicators: security_id={e.security_id}, "
                        f"from={e.start_date}, to={e.end_date}"
                    )
                    continue

                models = [
                    _map_indicators_df_to_model(
                        row._asdict() if hasattr(row, "_asdict") else row
                    )
                    for _, row in df.iterrows()
                ]

                technical_indicator_handler.save_all(models)
                db_session.commit()

            except Exception as e:
                Log.error(
                    f"Failed to compute indicators for {security.symbol} with id {security.id}: {e}"
                )


def heal_missing_technical_indicators() -> None:
    with next(get_db()) as db_session:
        security_handler = SecurityHandler(db_session)
        technical_indicator_handler = TechnicalIndicatorHandler(db_session)
        all_securities = security_handler.get_all()

        for security in all_securities:
            if security.exchange is None or security.first_trade_date is None:
                Log.warning(f"skipping {security.symbol} missing metadata.")
                continue

            try:
                trading_days = set(
                    get_all_trading_days_between(
                        exchange=security.exchange,
                        start=last_year(),
                        end=yesterday(),
                    )
                )

                existing_dates = (
                    technical_indicator_handler.get_dates_with_indicators_for_security(
                        security.id
                    )
                )
                missing_dates = sorted(list(trading_days - existing_dates))

                if not missing_dates:
                    Log.info(f"No indicator gaps for {security.symbol}")
                    continue

                Log.info(
                    f"Found {len(missing_dates)} indicator gaps for {security.symbol} "
                    f"between {min(missing_dates)} and {max(missing_dates)}."
                )

                try:
                    df = compute_indicators_for_range(
                        security_id=security.id,
                        start_date=min(missing_dates),
                        end_date=max(missing_dates),
                        session=db_session,
                    )
                except InsufficientOHLCVDataError as e:
                    Log.warning(
                        f"Insufficient OHLCV data for indicators: security_id={e.security_id}, "
                        f"from={e.start_date}, to={e.end_date}"
                    )
                    continue

                if df.empty:
                    continue

                models = [
                    _map_indicators_df_to_model(
                        row._asdict() if hasattr(row, "_asdict") else row
                    )
                    for _, row in df.iterrows()
                ]

                technical_indicator_handler.save_all(models)
                db_session.commit()

            except InvalidOperation as e:
                # tb = traceback.format_exc()
                Log.error(
                    f"Caught decimal error while processing {security.symbol}: {e}"
                )
            except Exception as e:
                Log.error(f"Failed healing indicators for {security.symbol}: {e}")


def _map_indicators_df_to_model(computed_values: dict) -> TechnicalIndicator:
    """
    Map indicator row(s) to a list of TechnicalIndicator models.
    Currently supports one row (latest measurement).
    """

    tc = TechnicalIndicator(
        measurement_date=computed_values["measurement_date"],
        security_id=computed_values["security_id"],
        sma_20=_to_float(computed_values.get("sma_20")),
        sma_50=_to_float(computed_values.get("sma_50")),
        sma_200=_to_float(computed_values.get("sma_200")),
        ema_9=_to_float(computed_values.get("ema_9")),
        ema_20=_to_float(computed_values.get("ema_20")),
        rsi_14=_to_float(computed_values.get("rsi_14")),
        high_10d=_to_float(computed_values.get("high_10d")),
        low_10d=_to_float(computed_values.get("low_10d")),
        avg_vol_20d=_to_float(computed_values.get("avg_vol_20d")),
        macd=_to_float(computed_values.get("macd")),
        macd_signal=_to_float(computed_values.get("macd_signal")),
        macd_hist=_to_float(computed_values.get("macd_hist")),
        atr_14=_to_float(computed_values.get("atr_14")),
        close_position=_to_float(computed_values.get("close_position")),
    )

    return tc


def _to_float(value) -> Optional[float]:
    return float(value) if pd.notna(value) else None
