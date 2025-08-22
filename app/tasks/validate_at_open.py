from datetime import date
from typing import Dict, List

import pandas as pd

from sqlmodel import Session

from app.core.db import get_db
from app.handlers.eod_signal import EODSignalHandler
from app.handlers.security import SecurityHandler
from app.handlers.technical_indicator import TechnicalIndicatorHandler
from app.models.eod_signal import EODSignal
from app.services.market_data_service import MarketDataService
from app.signals.filters import (
    apply_default_open_validation_filters,
    apply_validate_at_open_filters,
)
from app.strategies import STRATEGY_PROVIDER
from app.utils.log_wrapper import Log
from app.utils.trading_calendar import get_nth_previous_trading_day


def validate_signals_from_previous_trading_day():
    today = date.today()
    previous_trading_day = get_nth_previous_trading_day(
        exchange="NYSE", as_of=today, lookback_days=1
    )

    # --- load signals + tickers
    with next(get_db()) as db_session:
        signals = EODSignalHandler(db_session).get_unvalidated_for_date(
            previous_trading_day
        )

        df = _create_signal_validation_dataframe(
            signals, previous_trading_day, today, db_session
        )

    # --- validate (pure)
    validated = apply_at_open_filters(df)

    # --- persist results
    _persist_validation_results(signals, validated)


def apply_at_open_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pure function: no DB/network. Doesn’t mutate input.
    Returns a copy with a new column: validated_at_open (bool|None).
      - None => missing next_open (not validated yet)
      - True/False => result of default + strategy-specific open filters
    """
    if df.empty:
        out = df.copy()
        out["validated_at_open"] = pd.Series([None] * 0, dtype="object")
        return out

    out = df.copy()

    # Mark rows with no open as unvalidated (None)
    missing_open = out["next_open"].isna()
    out["validated_at_open"] = None

    validated_ids: set[int] = set()

    for strat_id, grp in out[~missing_open].groupby("strategy_id", sort=False):
        cfg = STRATEGY_PROVIDER.get_by_id(strat_id)

        # 1) Default open validation filters
        required = cfg.required_sod_columns()
        base = apply_default_open_validation_filters(grp.copy(), required)
        if base.empty:
            continue

        # 2) Strategy-specific open filters
        working = base.copy()
        # working["open"] = working["next_open"]  # alias
        passed = apply_validate_at_open_filters(working, cfg)

        if "id" in passed.columns:
            validated_ids.update(passed["id"].tolist())

    # Fill validated_at_open column
    mask_known = ~missing_open
    out.loc[mask_known, "validated_at_open"] = out.loc[mask_known, "id"].isin(
        validated_ids
    )

    return out


def _attach_early_ohlcvs_5m(df: pd.DataFrame, on_date: date) -> pd.DataFrame:
    symbols = df["symbol"].dropna().unique().tolist()
    bars = MarketDataService.fetch_early_ohlcvs_5m(symbols, on_date=on_date)
    out = df.copy()
    out["next_open"] = out["symbol"].map(lambda s: (bars.get(s) or {}).get("open"))
    out["early_volume"] = out["symbol"].map(lambda s: (bars.get(s) or {}).get("volume"))
    return out


def _persist_validation_results(signals, validated_df: pd.DataFrame) -> None:
    # Build quick lookups
    next_open_by_id = pd.Series(
        validated_df["next_open"].values, index=validated_df["id"].values
    ).to_dict()
    valid_by_id = pd.Series(
        validated_df["validated_at_open"].values, index=validated_df["id"].values
    ).to_dict()

    with next(get_db()) as db:
        for sig in signals:
            nid = sig.id
            sig.next_open_price = next_open_by_id.get(nid)
            sig.validated_at_open = valid_by_id.get(nid)  # None/True/False
        db.add_all(signals)
        db.commit()


def _create_signal_validation_dataframe(
    signals: List[EODSignal],
    previous_trading_day: date,
    today: date,
    db_session: Session,
) -> pd.DataFrame:

    if not signals:
        Log.info("No signals found to validate.")
        return pd.DataFrame()

    sec_ids = [s.security_id for s in signals]
    securities = SecurityHandler(db_session).get_by_ids(sec_ids)
    sec_id_to_symbol: Dict[int, str] = {s.id: s.symbol for s in securities}

    combined_rows = TechnicalIndicatorHandler(
        db_session
    ).get_combined_data_by_date_and_security_ids(previous_trading_day, sec_ids)

    sig_df = pd.DataFrame(
        [s.model_dump() for s in signals]
    )  # must include: id, security_id, strategy_id
    sig_df["symbol"] = sig_df["security_id"].map(sec_id_to_symbol)

    comb_df = pd.DataFrame([r.model_dump() for r in combined_rows])
    df = sig_df.merge(comb_df, on="security_id", how="left")

    # --- attach market data
    df = _attach_early_ohlcvs_5m(df, on_date=today)

    return df
