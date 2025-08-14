from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlmodel import Session, select

from app.core.db import upsert  # your existing helper
from app.models.eod_signal import EODSignal

UNIQUE_CONSTRAINT = "uq_one_result_per_strategy_and_security"


@dataclass
class EODSignalHandler:
    db_session: Session

    def save_all(self, rows: list[EODSignal]) -> None:
        if not rows:
            return

        upsert(
            model=EODSignal,
            db_session=self.db_session,
            data_iter=rows,
            constraint=UNIQUE_CONSTRAINT,
            exclude_columns={"id", "created_at", "updated_at"},
        )
        self.db_session.flush()

    def get_unvalidated_for_date(self, signal_date: date) -> list[EODSignal]:
        stmt = select(EODSignal).where(
            EODSignal.signal_date == signal_date, EODSignal.validated_at_open is None
        )

        return self.db_session.exec(stmt).all()
