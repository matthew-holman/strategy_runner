from dataclasses import dataclass
from typing import List

from sqlmodel import Session

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
