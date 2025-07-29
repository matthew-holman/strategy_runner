from dataclasses import dataclass
from datetime import date
from typing import List

from sqlmodel import Session, select

from app.models.stock_index_constituent import (
    StockIndexConstituent,
    StockIndexConstituentCreate,
)
from app.models.stock_index_snapshot import StockIndexSnapshot


@dataclass
class StockIndexConstituentHandler:
    db_session: Session

    def snapshot_matches_most_recent(self, index_name: str, snapshot_hash: str) -> bool:
        stmt = (
            select(StockIndexSnapshot)
            .where(StockIndexSnapshot.index_name == index_name)
            .order_by(StockIndexSnapshot.snapshot_date.desc())  # type: ignore[attr-defined]
            .limit(1)
        )
        last_snapshot = self.db_session.exec(stmt).first()
        return (
            last_snapshot is not None and last_snapshot.snapshot_hash == snapshot_hash
        )

    def get_earliest_snapshot(self, index_name: str) -> StockIndexSnapshot:
        stmt = (
            select(StockIndexSnapshot)
            .where(StockIndexSnapshot.index_name == index_name)
            .order_by(StockIndexSnapshot.snapshot_date.asc())  # type: ignore[attr-defined]
            .limit(1)
        )
        return self.db_session.exec(stmt).first()

    def get_most_recent_snapshot(self, index_name: str) -> StockIndexSnapshot:
        stmt = (
            select(StockIndexSnapshot)
            .where(StockIndexSnapshot.index_name == index_name)
            .order_by(StockIndexSnapshot.snapshot_date.desc())  # type: ignore[attr-defined]
            .limit(1)
        )
        return self.db_session.exec(stmt).first()

    def get_by_snapshot_id(self, snapshot_id: int) -> List[StockIndexConstituent]:
        stmt = select(StockIndexConstituent).where(
            StockIndexConstituent.snapshot_id == snapshot_id
        )
        return self.db_session.exec(stmt)

    def save_all(self, index_constituents: List[StockIndexConstituentCreate]) -> None:
        ics = [StockIndexConstituent.model_validate(ic) for ic in index_constituents]
        self.db_session.add_all(ics)
        self.db_session.flush()

    def save_snapshot(
        self, index_name: str, snapshot_hash: str, snapshot_date: date
    ) -> StockIndexSnapshot:
        snapshot = StockIndexSnapshot(
            index_name=index_name,
            snapshot_hash=snapshot_hash,
            snapshot_date=snapshot_date,
        )
        self.db_session.add(snapshot)
        self.db_session.flush()
        return snapshot
