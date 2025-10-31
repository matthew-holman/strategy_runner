from datetime import date
from decimal import InvalidOperation
from typing import Optional

import pandas as pd

from dateutil.utils import today

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
    _generate_indicators_for_range(
        start_date=compute_date,
        end_date=compute_date,
        context="EOD",
    )


def heal_missing_technical_indicators() -> None:
    with next(get_db()) as db_session:
        security_handler = SecurityHandler(db_session)
        all_securities = security_handler.get_all()

        for security in all_securities:
            if security.exchange is None or security.first_trade_date is None:
                Log.warning(f"[HEAL] Skipping {security.symbol}: missing metadata.")
                continue

            trading_days = set(
                get_all_trading_days_between(
                    exchange=security.exchange,
                    start=last_year(),
                    end=today(),
                )
            )

            indicator_handler = TechnicalIndicatorHandler(db_session)
            existing_dates = indicator_handler.get_dates_with_indicators_for_security(
                security.id
            )
            missing_dates = sorted(list(trading_days - existing_dates))

            if not missing_dates:
                Log.info(f"[HEAL] No indicator gaps for {security.symbol}")
                continue

            start_date = min(missing_dates)
            end_date = max(missing_dates)

            Log.info(
                f"[HEAL] Healing indicators for {security.symbol} ({start_date} → {end_date})"
            )
            _generate_indicators_for_range(start_date, end_date, context="HEAL")


def recompute_indicators_for_all_securities(
    start_date: date,
    end_date: date = today(),
) -> None:
    _generate_indicators_for_range(start_date, end_date, context="RECOMPUTE")


def _generate_indicators_for_range(
    start_date: date,
    end_date: date,
    context: str,
) -> None:
    """
    Core reusable routine for computing and persisting indicators for all securities
    within a specified date range.

    Args:
        start_date: First trading date to compute indicators.
        end_date: Last trading date to compute indicators.
        context: Logging context (e.g. 'EOD', 'heal', 'recompute').
    """
    Log.info(f"[{context}] Computing indicators between {start_date} and {end_date}")

    with next(get_db()) as db_session:
        for security in SecurityHandler(db_session).get_all():
            try:
                df = compute_indicators_for_range(
                    security_id=security.id,
                    start_date=start_date,
                    end_date=end_date,
                    session=db_session,
                )

                if df.empty:
                    Log.debug(f"[{context}] No indicator data for {security.symbol}")
                    continue

                models = [
                    _map_indicators_df_to_model(
                        row._asdict() if hasattr(row, "_asdict") else row
                    )
                    for _, row in df.iterrows()
                ]

                TechnicalIndicatorHandler(db_session).save_all(models)
                db_session.commit()

            except InsufficientOHLCVDataError as e:
                Log.warning(
                    f"[{context}] Insufficient OHLCV data for {security.symbol}: "
                    f"{e.start_date} → {e.end_date}"
                )
                db_session.rollback()
                continue
            except InvalidOperation as e:
                Log.error(
                    f"[{context}] Decimal error while processing {security.symbol}: {e}"
                )
                db_session.rollback()
                continue
            except Exception as e:
                Log.error(
                    f"[{context}] Failed to compute indicators for {security.symbol}: {e}"
                )
                db_session.rollback()
                continue

    Log.info(f"[{context}] Completed indicator generation for all securities.")


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
        avg_vol_5d=_to_float(computed_values.get("avg_vol_5d")),
        avg_vol_20d=_to_float(computed_values.get("avg_vol_20d")),
        avg_vol_50d=_to_float(computed_values.get("avg_vol_50d")),
        avg_vol_weighted_change_5d=_to_float(
            computed_values.get("avg_vol_weighted_change_5d")
        ),
        avg_vol_weighted_change_50d=_to_float(
            computed_values.get("avg_vol_weighted_change_50d")
        ),
        macd=_to_float(computed_values.get("macd")),
        macd_signal=_to_float(computed_values.get("macd_signal")),
        macd_hist=_to_float(computed_values.get("macd_hist")),
        atr_14=_to_float(computed_values.get("atr_14")),
        close_position=_to_float(computed_values.get("close_position")),
        percent_change=_to_float(computed_values.get("percent_change")),
        price_volume_corr_20=_to_float(computed_values.get("price_volume_corr_20")),
        range_pct_20=_to_float(computed_values.get("range_pct_20")),
        breakout_proximity_20=_to_float(computed_values.get("breakout_proximity_20")),
        rolling_volatility_20=_to_float(computed_values.get("rolling_volatility_20")),
    )

    return tc


def _to_float(value) -> Optional[float]:
    return float(value) if pd.notna(value) else None
