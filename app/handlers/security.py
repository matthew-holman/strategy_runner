from dataclasses import dataclass

from models.security import Security
from sqlmodel import Session, select


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
