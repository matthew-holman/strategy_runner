from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.db import upsert
from app.models.ohlcv_daily import OHLCVDaily, OHLCVDailyCreate


@dataclass
class OHLCVDailyHandler:
    db_session: Session

    def save_all(self, new_candles: List[OHLCVDailyCreate]) -> None:
        if not new_candles:
            return

        upsert(
            model=OHLCVDaily,
            db_session=self.db_session,
            exclude_columns={"id", "created_at"},
            data_iter=new_candles,
            constraint="uq_ohlcv_daily_date_security",
        )
        self.db_session.flush()

    def get_latest_candle_date(self, security_id: int) -> Optional[date]:
        stmt = select(func.max(OHLCVDaily.candle_date)).where(
            OHLCVDaily.security_id == security_id
        )
        result = self.db_session.exec(stmt).one_or_none()
        return result if result else None

    def get_earliest_candle_date(self, security_id: int) -> Optional[date]:
        stmt = select(func.min(OHLCVDaily.candle_date)).where(
            OHLCVDaily.security_id == security_id
        )
        result = self.db_session.exec(stmt).one_or_none()
        return result if result else None

    def get_period_for_security(
        self, start: date, end: date, security_id: int
    ) -> List[OHLCVDaily]:
        stmt = select(OHLCVDaily).where(
            OHLCVDaily.security_id == security_id,
            OHLCVDaily.candle_date >= start,
            OHLCVDaily.candle_date <= end,
        )
        return self.db_session.exec(stmt).all()

    def get_dates_for_security(self, security_id: int) -> set[date]:
        stmt = (
            select(OHLCVDaily.candle_date)
            .where(OHLCVDaily.security_id == security_id)
            .distinct()
        )
        result = self.db_session.exec(stmt).all()
        return {row for row in result if row is not None}

    def get_open_for_security(
        self, candle_date: date, security_id: int
    ) -> float | None:
        stmt = select(OHLCVDaily.open).where(
            OHLCVDaily.security_id == security_id,
            OHLCVDaily.candle_date == candle_date,
        )
        return self.db_session.exec(stmt).first()
