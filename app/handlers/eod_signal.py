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

    def get_unvalidated_by_date_and_strategy(
        self, signal_date: date, strategy_id: str
    ) -> list[EODSignal]:
        stmt = select(EODSignal).where(
            EODSignal.strategy_id == strategy_id,
            EODSignal.signal_date == signal_date,
            EODSignal.validated_at_open.is_(None),  # type: ignore[union-attr]
        )

        return self.db_session.exec(stmt).all()

    def get_by_strategy_between_dates(
        self, strategy_id: str, start_date: date, end_date: date
    ) -> list[EODSignal]:
        stmt = select(EODSignal).where(
            EODSignal.strategy_id == strategy_id,
            EODSignal.signal_date >= start_date,
            EODSignal.signal_date <= end_date,
        )

        return self.db_session.exec(stmt).all()

    def get_all_strategy_between_dates(
        self, start_date: date, end_date: date
    ) -> list[EODSignal]:
        stmt = select(EODSignal).where(
            EODSignal.signal_date >= start_date,
            EODSignal.signal_date <= end_date,
        )

        return self.db_session.exec(stmt).all()

    def get_validated_by_strategy_between_dates(
        self, strategy_id: str, start_date: date, end_date: date
    ) -> list[EODSignal]:
        stmt = select(EODSignal).where(
            EODSignal.strategy_id == strategy_id,
            EODSignal.signal_date >= start_date,
            EODSignal.signal_date <= end_date,
            EODSignal.validated_at_open == True,  # noqa
        )

        return self.db_session.exec(stmt).all()

    def get_date_of_oldest_signal_for_strategy(self, strategy_id: str) -> date | None:
        stmt = (
            select(EODSignal.signal_date)
            .where(EODSignal.strategy_id == strategy_id)
            .order_by(EODSignal.signal_date.asc())  # type: ignore[attr-defined]
            .limit(1)
        )
        return self.db_session.exec(stmt).first()
