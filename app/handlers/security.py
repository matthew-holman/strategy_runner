from dataclasses import dataclass
from typing import List, Optional, Sequence

from sqlmodel import Session, or_, select

from app.models.security import Security


@dataclass
class SecurityHandler:
    db_session: Session

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

    def get_by_id(self, security_id: int) -> Optional[Security]:
        stmt = select(Security).where(Security.id == security_id)
        security = self.db_session.exec(stmt).first()
        if security:
            return security
        return None

    def get_with_missing_metadata(self) -> List[Security]:
        stmt = select(Security).where(
            or_(
                Security.first_trade_date.is_(None),  # type: ignore[union-attr]
                Security.exchange.is_(None),  # type: ignore[union-attr]
            )
        )
        return list(self.db_session.exec(stmt))
