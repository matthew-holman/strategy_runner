from dataclasses import dataclass
from typing import Optional, Sequence

from sqlmodel import Session, select

from app.models.security import Security


@dataclass
class SecurityHandler:
    db_session: Session

    def get_or_create(self, record: dict) -> Optional[Security]:
        stmt = select(Security).where(Security.symbol == record["symbol"])
        security = self.db_session.exec(stmt).first()
        if security:
            return security
        return None

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
