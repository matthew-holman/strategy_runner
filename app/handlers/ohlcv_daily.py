from dataclasses import dataclass
from datetime import date
from typing import Optional

from core.db import upsert
from models.ohlcv_daily import OHLCVDaily, OHLCVDailyCreate
from sqlalchemy import func
from sqlmodel import Session, select


@dataclass
class OHLCVDailyHandler:
    db_session: Session

    def save_all(self, new_candles: list[OHLCVDailyCreate]) -> None:
        if not new_candles:
            return

        upsert(
            model=OHLCVDaily,
            db_session=self.db_session,
            constraint="uq_ohlcv_daily_date_security",
            data_iter=new_candles,
            exclude_columns={"id", "created_at"},
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
