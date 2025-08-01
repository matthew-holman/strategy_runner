from datetime import date
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base_model import BaseModel


class MissingOHLCVDataEvent(BaseModel, table=True):  # type: ignore[call-arg]

    __tablename__ = "missing_ohlcv_data_event"

    id: Optional[int] = Field(default=None, primary_key=True)
    security_id: int = Field(foreign_key="security.id")
    start_date: date
    end_date: date
    handled: bool = Field(default=False)

    __table_args__ = (
        UniqueConstraint(
            "security_id", "start_date", "end_date", name="uq_security_start_end"
        ),
        {"extend_existing": True},
    )
