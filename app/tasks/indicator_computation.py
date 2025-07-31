from datetime import date
from typing import Optional

import pandas as pd

from app.core.db import get_db
from app.handlers.stock_index_constituent import StockIndexConstituentHandler
from app.handlers.technical_indicator import TechnicalIndicatorHandler
from app.indicators.compute import compute_all_indicators
from app.models.stock_index_constituent import SP500
from app.models.technical_indicator import TechnicalIndicator
from app.utils.log import Log


def compute_daily_indicators_for_all_securities(
    compute_date: date = date.today(),
) -> None:
    """
    Task: Compute and persist technical indicators for each security for a given date.

    Args:
        compute_date: The date to compute indicators for (default: today).
    """
    log = Log.setup("trading-bot", "indicator-task")
    log.info(f"Running indicator update for {compute_date}")

    with next(get_db()) as db_session:
        technical_indicator_handler = TechnicalIndicatorHandler(db_session)

        stock_ic_handler = StockIndexConstituentHandler(db_session)
        latest_sp500_snapshot = stock_ic_handler.get_most_recent_snapshot(SP500)

        if latest_sp500_snapshot.id is None:
            log.warning("No snapshot found for S&P 500.")
            return

        index_constituents = stock_ic_handler.get_by_snapshot_id(
            latest_sp500_snapshot.id
        )

        for index_constituent in index_constituents:
            security = index_constituent.security

            if security is None:
                log.warning(
                    f"Constituent {index_constituent.id} has no linked security"
                )
                continue

            try:
                df = compute_all_indicators(
                    security_id=security.id,
                    compute_date=compute_date,
                    session=db_session,
                )

                if df.empty:
                    log.warning(
                        f"No indicators computed for {security.id} on {compute_date}"
                    )
                    continue

                model = _map_indicators_df_to_model(df.to_dict())
                technical_indicator_handler.save_all([model])
                db_session.commit()

            except Exception as e:
                log.error(
                    f"Failed to compute indicators for {security.symbol} with id {security.id}: {e}"
                )


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
