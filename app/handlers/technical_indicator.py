from dataclasses import dataclass
from datetime import date
from typing import List

from sqlmodel import Session, select

from app.core.db import upsert
from app.models.technical_indicator import TechnicalIndicator


@dataclass
class TechnicalIndicatorHandler:
    db_session: Session

    def save_all(self, technical_indicators: List[TechnicalIndicator]) -> None:
        if not technical_indicators:
            return

        upsert(
            model=TechnicalIndicator,
            db_session=self.db_session,
            index_elements=["security_id", "measurement_date"],
            data_iter=technical_indicators,
            exclude_columns={"created_at"},
        )
        self.db_session.flush()

    def get_dates_for_security(self, security_id: int) -> set[date]:
        stmt = (
            select(TechnicalIndicator.measurement_date)
            .where(TechnicalIndicator.security_id == security_id)
            .distinct()
        )
        result = self.db_session.exec(stmt)
        return {row for row in result if row is not None}
