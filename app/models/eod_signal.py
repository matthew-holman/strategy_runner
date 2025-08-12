from datetime import date
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlmodel import Field, Relationship

from app.models.base_model import BaseModel
from app.models.ohlcv_daily import OHLCVDaily
from app.models.technical_indicator import TechnicalIndicator


class EODSignalBase(BaseModel, table=False):  # type: ignore[call-arg]
    # Core identity
    signal_date: date = Field(
        index=True, description="Trading day this signal is based on"
    )
    strategy_name: str = Field(description="Strategy that generated the signal")

    # joins
    security_id: int = Field(index=True, foreign_key="security.id")
    ohlcv_daily_id: int = Field(foreign_key="ohlcv_daily.id")

    # Scoring / diagnostics
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="raw score from strategy logic before ranking weights",
    )
    notes: Optional[str] = Field(
        default=None, description="Short explanation of why it passed"
    )


class EODSignal(EODSignalBase, table=True):  # type: ignore[call-arg]

    __tablename__ = "eod_signal"

    id: int = Field(default=None, primary_key=True)

    __table_args__ = (
        UniqueConstraint(
            "signal_date",
            "strategy_name",
            "security_id",
            name="uq_one_result_per_strategy_and_security",
        ),
        CheckConstraint("score >= 0.0 AND score <= 1.0", name="ck_score_range"),
        ForeignKeyConstraint(
            ["security_id", "signal_date"],
            ["technical_indicator.security_id", "technical_indicator.measurement_date"],
            name="fk_eod_signal_technical_indicator",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        {"extend_existing": True},
    )

    ohlcv_daily: Optional[OHLCVDaily] = Relationship(back_populates="eod_signals")
    technical_indicator: Optional[TechnicalIndicator] = Relationship(
        back_populates="eod_signals"
    )
