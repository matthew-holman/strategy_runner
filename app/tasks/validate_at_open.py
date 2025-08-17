from datetime import date

import pandas as pd

from app.core.db import get_db
from app.handlers.eod_signal import EODSignalHandler
from app.services.market_data_service import MarketDataService
from app.signals.filters import (
    apply_default_open_validation_filters,
    apply_validate_at_open_filters,
)
from app.strategies import STRATEGY_PROVIDER
from app.utils import Log
from app.utils.trading_calendar import get_nth_previous_trading_day

log = Log.setup(log_name="sod-tasks", application_name="daily-tasks")


def validate_signals_from_previous_trading_day():

    today = date.today()
    previous_trading_day = get_nth_previous_trading_day(
        exchange="NYSE", as_of=today, lookback_days=1
    )

    with next(get_db()) as db_session:
        signals_to_validate = EODSignalHandler(db_session).get_unvalidated_for_date(
            previous_trading_day
        )

        if not signals_to_validate:
            log.error("No signals found to validate.")

        # security_ids = [s.security_id for s in signals_to_validate]
        # securities = SecurityHandler(db_session).get_by_ids(
        #     security_ids
        # )  # implement if you don’t have it
        # sec_by_id: Dict[int, str] = {s.id: s.ticker for s in securities}
        #
        # rows = TechnicalIndicatorHandler(
        #     db_session
        # ).get_combined_data_by_date_and_security_ids(previous_trading_day, security_ids)

        df = pd.DataFrame([signal.model_dump() for signal in signals_to_validate])
        df = _attach_next_open(df, on_date=today)
        df = _attach_early_volume(df, on_date=today)

        passed_frames = []
        for strategy_id, _grp in df.groupby("strategy_id", sort=False):
            strategy_config = STRATEGY_PROVIDER.get_by_id(strategy_id)
            required_cols = strategy_config.required_eod_columns()

            base = apply_default_open_validation_filters(df, required_cols)
            if base.empty:
                continue
            validated = apply_validate_at_open_filters(base, strategy_config)
            passed_frames.append(validated)

        out = (
            pd.concat(passed_frames, ignore_index=True)
            if passed_frames
            else pd.DataFrame()
        )

        return out


def _attach_next_open(df: pd.DataFrame, on_date: date) -> pd.DataFrame:
    tickers = df["ticker"].dropna().unique().tolist()
    opens = MarketDataService().fetch_daily_open_for_ticker(tickers, on_date=on_date)
    out = df.copy()
    out["next_open"] = out["ticker"].map(opens)
    return out


def _attach_early_volume(df: pd.DataFrame, on_date: date) -> pd.DataFrame:
    tickers = df["ticker"].dropna().unique().tolist()
    early_vol_by_ticker = MarketDataService.fetch_early_volumes_5m(
        tickers, on_date=on_date
    )
    out = df.copy()
    out["early_volume"] = out["ticker"].map(early_vol_by_ticker)
    return out
