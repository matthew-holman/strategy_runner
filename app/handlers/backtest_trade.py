from dataclasses import dataclass
from typing import List

from sqlmodel import Session

from app.core.db import upsert
from app.models.backtest_trade import BacktestTrade

UNIQUE_CONSTRAINT = "uq_backtest_trade_signal_execution_strategy_per_run"


@dataclass
class BacktestTradeHandler:
    db_session: Session

    def save_all(self, rows: List[BacktestTrade]) -> List[BacktestTrade]:
        """
        Bulk upsert BacktestTrade rows using the unique constraint (run_id, eod_signal_id).
        Returns the updated/inserted BacktestTrade objects as loaded from the DB.
        """
        if not rows:
            return []
        return upsert(
            model=BacktestTrade,
            db_session=self.db_session,
            exclude_columns={"id", "created_at", "updated_at"},
            data_iter=list(rows),
            constraint=UNIQUE_CONSTRAINT,
        )
