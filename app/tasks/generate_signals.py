import json

from datetime import date
from pathlib import Path
from typing import List, Set

import pandas as pd

from handlers.eod_signal_handler import EODSignalHandler
from models.eod_signal import EODSignal
from utils import Log

from app.core.db import get_db
from app.handlers.security import SecurityHandler
from app.handlers.stock_index_constituent import StockIndexConstituentHandler
from app.handlers.technical_indicator import TechnicalIndicatorHandler
from app.models.stock_index_constituent import SP500
from app.models.strategy_config import StrategyConfig
from app.signals.filters import apply_default_filters, apply_strategy_filters
from app.signals.ranking import apply_strategy_ranking
from app.utils.datetime_utils import yesterday

BASE_CONFIG_DIR = Path(__file__).parent / ".." / ".." / "strategy_configs"
REQUIRED_COLS: Set[str] = {"security_id", "measurement_date", "ohlcv_daily_id", "score"}


def run_signal_picker(generation_date: date, strategy_config: StrategyConfig):

    with next(get_db()) as db_session:
        snapshot = StockIndexConstituentHandler(
            db_session
        ).get_relevant_snapshot_for_date(generation_date, SP500)

        if snapshot is None or snapshot.id is None:
            raise ValueError("Snapshot returned was empty")

        tickers = SecurityHandler(db_session).get_by_snapshot_id(snapshot.id)

        indicator_data = TechnicalIndicatorHandler(
            db_session
        ).get_combined_data_by_date_and_security_ids(
            generation_date, [ticker.id for ticker in tickers]
        )

        df = pd.DataFrame([ti.model_dump() for ti in indicator_data])

        required_cols = strategy_config.required_columns()
        default_filtered = apply_default_filters(df, required_cols)
        Log.info(
            f"{len(df) - len(default_filtered)} tickers removed by default filtering."
        )

        strategy_filtered = apply_strategy_filters(default_filtered, strategy_config)
        Log.info(
            f"{len(strategy_filtered)} tickers remaining after applying {strategy_config.name} filters."
        )

        ranked_signals = apply_strategy_ranking(strategy_filtered, strategy_config)

        Log.info(
            f"Found {len(ranked_signals)} using strategy {strategy_config.name}, persisting to db."
        )
        EODSignalHandler(db_session).save_all(
            _map_ranked_df_to_eod_signals(ranked_signals, strategy_config.name)
        )
        db_session.commit()


def generate_daily_signals(strategy_json_path: str):
    # Load and parse the JSON file
    full_path = (BASE_CONFIG_DIR / strategy_json_path).resolve()

    with open(full_path) as f:
        raw_config = json.load(f)

    # Validate and parse into a StrategyConfig
    strategy_config = StrategyConfig.model_validate(raw_config)

    # Run the signal picker for yesterdays trading
    return run_signal_picker(
        generation_date=yesterday(), strategy_config=strategy_config
    )


def _map_ranked_df_to_eod_signals(
    ranked_df: pd.DataFrame,
    strategy_name: str,
) -> List[EODSignal]:
    """
    Convert ranked signal dataframe into EODSignal models (no persistence).

    Expects ranked_df to include (at minimum):
      - security_id: int
      - measurement_date: date (your signal_date)
      - ohlcv_daily_id: int
      - score: float in [0, 1]
      - notes: optional[str]

    Returns a list[EODSignal] ready for persistence.
    """
    missing = REQUIRED_COLS - set(ranked_df.columns)
    if missing:
        raise ValueError(f"ranked_df missing required columns: {sorted(missing)}")

    # Optional dedupe by (signal_date, strategy_name, security_id) in case caller sent dupes
    ranked_df = ranked_df.drop_duplicates(
        subset=["measurement_date", "security_id"], keep="first"
    )

    out: List[EODSignal] = []
    for row in ranked_df.itertuples(index=False):
        out.append(
            EODSignal(
                signal_date=row.measurement_date,
                strategy_name=strategy_name,
                security_id=int(row.security_id),
                ohlcv_daily_id=int(row.ohlcv_daily_id),
                score=float(row.score),
                notes=getattr(row, "notes", None),  # still fine for optional
            )
        )
    return out
