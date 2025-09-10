from datetime import date, timedelta
from typing import Dict, List

import pandas as pd

from dateutil.utils import today
from handlers.ohlcv_daily import OHLCVDailyHandler
from sqlmodel import Session

from app.core.db import get_db
from app.handlers.eod_signal import EODSignalHandler
from app.handlers.security import SecurityHandler
from app.handlers.technical_indicator import TechnicalIndicatorHandler
from app.models.eod_signal import EODSignal
from app.models.signal_strategy import SignalStrategy
from app.services.market_data_service import MarketDataService
from app.signals.filters import (
    apply_default_open_validation_filters,
    apply_validate_at_open_filters,
)
from app.utils.datetime_utils import chunk_date_range
from app.utils.log_wrapper import Log
from app.utils.trading_calendar import get_nth_trading_day


def validate_historic_signals_for_strategy_at_open(
    signal_strategy: SignalStrategy,
):
    Log.info(
        f"[AT_OPEN/HIST] Begin validation for strategy_id={signal_strategy.strategy_id} "
        f"name='{signal_strategy.name}'"
    )

    with next(get_db()) as db_session:
        eod_signal_handler = EODSignalHandler(db_session)
        oldest_signal_date = eod_signal_handler.get_date_of_oldest_signal_for_strategy(
            signal_strategy.strategy_id
        )

        if oldest_signal_date is None:
            Log.info(
                f"[AT_OPEN/HIST] No historical signals found for {signal_strategy.strategy_id}; nothing to validate."
            )
            return

        for _chunk_start, chunk_end in chunk_date_range(
            oldest_signal_date, today().date(), timedelta(days=1)
        ):

            signals = EODSignalHandler(db_session).get_unvalidated_by_date_and_strategy(
                chunk_end, signal_strategy.strategy_id
            )
            if not signals:
                # no signals for day, skip to next day
                continue

            next_trading_day = get_nth_trading_day(
                exchange="NYSE", as_of=chunk_end, offset=1
            )

            df = _create_initial_validation_dataframe(signals, chunk_end, db_session)

            if df.empty:
                Log.warning(
                    f"[AT_OPEN/HIST] {chunk_end}: initial dataframe is empty after join; "
                    f"skipping {len(signals)} signals."
                )
                continue

            df = _attach_historic_next_day_ohlcv(
                df=df, on_date=next_trading_day, db_session=db_session
            )
            # --- validate (pure)
            validated = apply_at_open_filters(df, signal_strategy)

            # --- persist results
            _persist_validation_results(signals, validated, db_session)
            db_session.commit()


def validate_signals_from_previous_trading_day(
    signal_strategy: SignalStrategy,
):
    trading_day = date.today()
    previous_trading_day = get_nth_trading_day(
        exchange="NYSE", as_of=trading_day, offset=-1
    )

    # --- load signals + tickers
    with next(get_db()) as db_session:
        signals = EODSignalHandler(db_session).get_unvalidated_by_date_and_strategy(
            previous_trading_day, signal_strategy.strategy_id
        )

        df = _create_initial_validation_dataframe(
            signals, previous_trading_day, db_session
        )
        df = _attach_early_ohlcvs_5m(df, on_date=trading_day)
    # --- validate (pure)
    validated = apply_at_open_filters(df, signal_strategy)

    # --- persist results
    _persist_validation_results(signals, validated, db_session)
    db_session.commit()


def apply_at_open_filters(
    df: pd.DataFrame, signal_strategy: SignalStrategy
) -> pd.DataFrame:
    """
    Pure function: no DB/network. Doesn’t mutate input.
    Assumes all rows belong to the provided signal_strategy.

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

    # Work only with rows that have next_open
    working = out[~missing_open].copy()
    if not working.empty:
        # 1) Default open validation filters (require strategy's SOD columns)
        required_columns = signal_strategy.required_sod_columns()
        base = apply_default_open_validation_filters(working.copy(), required_columns)

        validated_ids: set[int] = set()
        if not base.empty:
            # 2) Strategy-specific open filters
            passed = apply_validate_at_open_filters(base.copy(), signal_strategy)
            if "id" in passed.columns:
                validated_ids.update(passed["id"].tolist())

        # Fill validated_at_open for known rows
        out.loc[~missing_open, "validated_at_open"] = out.loc[~missing_open, "id"].isin(
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


def _persist_validation_results(
    signals, validated_df: pd.DataFrame, db_session: Session
) -> None:
    # Build quick lookups
    next_open_by_id = pd.Series(
        validated_df["next_open"].values, index=validated_df["id"].values
    ).to_dict()
    valid_by_id = pd.Series(
        validated_df["validated_at_open"].values, index=validated_df["id"].values
    ).to_dict()

    for sig in signals:
        nid = sig.id
        sig.next_open_price = next_open_by_id.get(nid)
        sig.validated_at_open = valid_by_id.get(nid)  # None/True/False
    db_session.add_all(signals)


def _create_initial_validation_dataframe(
    signals: List[EODSignal],
    signal_date: date,
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
    ).get_combined_data_by_date_and_security_ids(signal_date, sec_ids)

    sig_df = pd.DataFrame(
        [s.model_dump() for s in signals]
    )  # must include: id, security_id, strategy_id
    sig_df["symbol"] = sig_df["security_id"].map(sec_id_to_symbol)

    comb_df = pd.DataFrame([r.model_dump() for r in combined_rows])
    df = sig_df.merge(comb_df, on="security_id", how="left")

    return df


def _attach_historic_next_day_ohlcv(
    df: pd.DataFrame, on_date: date, db_session: Session
) -> pd.DataFrame:
    """
    Attach the stored next-day open to each row as 'next_open'.
    Looks up OHLCV for `on_date` for every security_id present in df.
    """
    if df.empty:
        out = df.copy()
        out["next_open"] = pd.Series(dtype="float64")
        return out

    # Ensure we have the key column
    if "security_id" not in df.columns:
        raise ValueError(
            "Expected 'security_id' column to be present in the dataframe."
        )

    security_ids: list[int] = [
        int(x) for x in df["security_id"].dropna().unique().tolist()
    ]
    if not security_ids:
        out = df.copy()
        out["next_open"] = pd.Series(dtype="float64")
        return out

    next_open_by_security_id: Dict[int, float | None] = {}

    for security_id in security_ids:
        next_open = OHLCVDailyHandler(db_session).get_open_for_security(
            on_date, security_id
        )
        if next_open:
            try:
                next_open_by_security_id[security_id] = float(next_open)
            except Exception:
                # Defensive: if schema/object shape changes
                Log.warning(
                    f"[AT_OPEN/HIST] Could not parse open for security_id={security_id} on {on_date}"
                )
                next_open_by_security_id[security_id] = None
        else:
            Log.info(
                f"[AT_OPEN/HIST] Missing OHLCV for security_id={security_id} on {on_date}; next_open=None"
            )
            next_open_by_security_id[security_id] = None

    out = df.copy()
    out["next_open"] = out["security_id"].map(
        lambda sid: next_open_by_security_id.get(int(sid), None)
    )
    return out
