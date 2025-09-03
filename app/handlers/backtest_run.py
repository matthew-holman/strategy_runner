from dataclasses import dataclass

from sqlmodel import Session

from app.models.backtest_run import BacktestRun


@dataclass
class BacktestRunHandler:
    db_session: Session

    def save(
        self,
        backtest_run: BacktestRun,
    ) -> BacktestRun:
        self.db_session.add(backtest_run)
        self.db_session.flush()
        return backtest_run
