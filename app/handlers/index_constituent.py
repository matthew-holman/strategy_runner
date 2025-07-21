from dataclasses import dataclass
from datetime import date
from typing import List

from models.index_constituent import (
    IndexConstituent,
    IndexConstituentCreate,
)
from models.index_snapshot import IndexSnapshot
from sqlmodel import Session, select


@dataclass
class IndexConstituentHandler:
    db_session: Session

    def snapshot_matches_most_recent(self, index_name: str, snapshot_hash: str) -> bool:
        stmt = (
            select(IndexSnapshot)
            .where(IndexSnapshot.index_name == index_name)
            .order_by(IndexSnapshot.snapshot_date.desc())
            .limit(1)
        )
        last_snapshot = self.db_session.exec(stmt).first()
        return (
            last_snapshot is not None and last_snapshot.snapshot_hash == snapshot_hash
        )

    def get_earliest_snapshot(self, index_name: str) -> IndexSnapshot:
        stmt = (
            select(IndexSnapshot)
            .where(IndexSnapshot.index_name == index_name)
            .order_by(IndexSnapshot.snapshot_date.asc())
            .limit(1)
        )
        return self.db_session.exec(stmt).first()

    def save_all(self, index_constituents: List[IndexConstituentCreate]) -> None:
        ics = [IndexConstituent.model_validate(ic) for ic in index_constituents]
        self.db_session.add_all(ics)
        self.db_session.commit()

    def save_snapshot(
        self, index_name: str, snapshot_hash: str, snapshot_date: date
    ) -> None:
        snapshot = IndexSnapshot(
            index_name=index_name,
            snapshot_hash=snapshot_hash,
            snapshot_date=snapshot_date,
        )
        self.db_session.add(snapshot)
        self.db_session.commit()
