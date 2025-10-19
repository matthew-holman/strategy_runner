from dataclasses import dataclass
from typing import List, Optional, Sequence

from sqlmodel import Session, or_, select

from app.core.db import upsert
from app.models.security import Region, Security
from app.models.stock_index_constituent import StockIndexConstituent

UNIQUE_CONSTRAINT = "uq_security_symbol"


@dataclass
class SecurityHandler:
    db_session: Session

    def save_all(self, rows: list[Security]) -> None:
        if not rows:
            return

        upsert(
            model=Security,
            db_session=self.db_session,
            data_iter=rows,
            constraint=UNIQUE_CONSTRAINT,
            exclude_columns={"id", "created_at", "updated_at"},
        )
        self.db_session.flush()

    def get_or_create(self, record: dict) -> Security:
        stmt = select(Security).where(Security.symbol == record["symbol"])
        security = self.db_session.exec(stmt).first()
        if security:
            return security

        new_security = Security.model_validate(record)
        self.db_session.add(new_security)
        self.db_session.flush()
        return new_security

    def get_all(self) -> Sequence[Security]:
        stmt = select(Security)
        return self.db_session.exec(stmt).all()

    def get_all_for_region(self, region: Region) -> Sequence[Security]:
        stmt = select(Security).where(Security.region == region)
        return self.db_session.exec(stmt).all()

    def get_all_symbols_for_region(self, region: Region) -> Sequence[Security]:
        stmt = select(Security.symbol).where(Security.region == region)
        return self.db_session.exec(stmt).all()

    def get_by_id(self, security_id: int) -> Optional[Security]:
        stmt = select(Security).where(Security.id == security_id)
        security = self.db_session.exec(stmt).first()
        if security:
            return security
        return None

    def get_by_ids(self, security_ids: List[int]) -> Sequence[Security]:
        stmt = select(Security).where(Security.id.in_(security_ids))  # type: ignore[attr-defined]
        return self.db_session.exec(stmt).all()

    def get_with_missing_metadata(self) -> List[Security]:
        stmt = select(Security).where(
            or_(
                Security.first_trade_date.is_(None),  # type: ignore[union-attr]
                Security.exchange.is_(None),  # type: ignore[union-attr]
            )
        )
        return list(self.db_session.exec(stmt))

    def get_by_snapshot_id(self, snapshot_id: int) -> List[Security]:
        stmt = select(Security, StockIndexConstituent).where(
            Security.id == StockIndexConstituent.security_id,
            StockIndexConstituent.snapshot_id == snapshot_id,
        )
        return [security for security, _ in self.db_session.exec(stmt)]
