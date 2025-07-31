from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Column, UniqueConstraint
from sqlmodel import Field

from app.models.base_model import BaseModel


class OHLCVDailyBase(BaseModel, table=False):  # type: ignore[call-arg]
    candle_date: date = Field(index=True)
    open: Decimal = Field(max_digits=10, decimal_places=2)
    high: Decimal = Field(max_digits=10, decimal_places=2)
    low: Decimal = Field(max_digits=10, decimal_places=2)
    close: Decimal = Field(max_digits=10, decimal_places=2)
    adjusted_close: Decimal = Field(max_digits=10, decimal_places=2)
    volume: int = Field(ge=0, sa_column=Column(BigInteger()))

    security_id: int = Field(foreign_key="security.id", index=True)


class OHLCVDaily(OHLCVDailyBase, table=True):  # type: ignore[call-arg]
    __tablename__ = "ohlcv_daily"

    id: int = Field(default=None, primary_key=True)

    __table_args__ = (
        UniqueConstraint(
            "candle_date", "security_id", name="uq_ohlcv_daily_date_security"
        ),
        {"extend_existing": True},
    )


class OHLCVDailyCreate(OHLCVDailyBase):  # type: ignore[call-arg]
    pass


class OHLCVDailyRead(OHLCVDailyBase):  # type: ignore[call-arg]
    id: int
