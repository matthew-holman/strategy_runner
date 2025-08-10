from dataclasses import dataclass
from datetime import date
from typing import List

from models.ohlcv_daily import OHLCVDaily
from sqlmodel import Session, select

from app.core.db import upsert
from app.models.technical_indicator import CombinedSignalRow, TechnicalIndicator


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

    def get_dates_with_indicators_for_security(self, security_id: int) -> set[date]:
        stmt = (
            select(TechnicalIndicator.measurement_date)
            .where(TechnicalIndicator.security_id == security_id)
            .distinct()
        )
        result = self.db_session.exec(stmt)
        return {row for row in result if row is not None}

    def get_by_date_and_security_ids(
        self, measurement_date: date, security_ids: List[int]
    ) -> List[TechnicalIndicator]:
        stmt = select(TechnicalIndicator).where(
            TechnicalIndicator.security_id.in_(security_ids),  # type: ignore[attr-defined]
            TechnicalIndicator.measurement_date == measurement_date,
        )
        return self.db_session.exec(stmt).all()

    def get_combined_data_by_date_and_security_ids(
        self, measurement_date: date, security_ids: list[int]
    ) -> list[CombinedSignalRow]:
        stmt = select(OHLCVDaily, TechnicalIndicator).where(
            OHLCVDaily.security_id == TechnicalIndicator.security_id,
            OHLCVDaily.candle_date == TechnicalIndicator.measurement_date,
            TechnicalIndicator.security_id.in_(security_ids),  # type: ignore[attr-defined]
            TechnicalIndicator.measurement_date == measurement_date,
        )

        results = self.db_session.exec(stmt).all()

        # Merge both model dicts into flat rows
        return [
            CombinedSignalRow(
                **ohlcv.model_dump(
                    by_alias=True,
                    exclude={"security_id", "candle_date", "created_at", "updated_at"},
                ),
                **ti.model_dump(exclude={"created_at", "updated_at"}),
            )
            for ohlcv, ti in results
        ]
