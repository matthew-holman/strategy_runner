from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Column, Field

from app.models.base_model import BaseModel


class EODSignalBase(BaseModel, table=False):  # type: ignore[call-arg]
    # Core identity
    signal_date: date = Field(
        index=True, description="Trading day this signal is based on"
    )
    strategy_name: str = Field(description="Strategy that generated the signal")
    strategy_id: str = Field(description="Matches filename, used for loading configs")

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
    validated_at_open: bool | None = Field(
        default=None,
        description="True/False after open validation; None if not yet validated",
        index=True,
    )
    next_open_price: Decimal | None = Field(  # use Decimal to avoid float drift
        default=None,
        description="Open price used during validation from the NEXT trading session",
    )
    validated_at_open_failures: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),  # Postgres ARRAY of TEXT
        description="List of rule codes that failed during open validation (empty if passed)",
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


class EODSignalRead(EODSignalBase, table=False):  # type: ignore[call-arg]
    id: int

    class Config:
        from_attributes = True
