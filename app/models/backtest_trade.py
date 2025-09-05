from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import false
from sqlmodel import Field, UniqueConstraint

from app.models.base_model import BaseModel


class ExitReason(str, Enum):
    stop = "stop"
    target = "target"
    time_stop = "time_stop"


@dataclass(frozen=True)
class ExitEvent:
    exit_date: date
    exit_price: float
    exit_reason: ExitReason
    bars_held: int  # counts the entry bar as 1


class EntryReason(str, Enum):
    IMMEDIATE_AT_OPEN = "immediate_at_open"
    WAIT_TRIGGER = "wait_trigger"
    # later: breakout_above, limit_at, touch_or_better, etc.


@dataclass(frozen=True)
class EntryEvent:
    entry_date: date
    price: float
    entry_reason: EntryReason
    bars_waited: int


class BacktestTradeBase(BaseModel, table=false()):  # type: ignore[call-arg]
    """
    One simulated trade produced by the backtesting runner.
    """

    run_id: UUID = Field(default_factory=uuid4, index=True)

    eod_signal_id: int = Field(foreign_key="eod_signal.id", index=True)
    signal_strategy_id: str = Field(index=True)
    execution_strategy_id: str = Field(index=True)
    security_id: int = Field(index=True)

    # Execution lifecycle
    entry_date: date = Field(index=True)
    exit_date: date = Field(index=True)
    exit_reason: ExitReason

    # Prices & sizing
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    atr_used: float

    # Results
    pnl_percent: float  # (exit_price / entry_price - 1) * 100
    r_multiple: float  # (exit_price - entry_price) / (entry_price - stop_price)
    bars_held: int  # number of bars from entry to exit; entry bar counts as 1


class BacktestTrade(BacktestTradeBase, table=True):  # type: ignore[call-arg]

    __tablename__ = "backtest_trade"

    id: int | None = Field(default=None, primary_key=True)
    __table_args__ = (
        # Prevent duplicate trades for the same signal within one run
        UniqueConstraint(
            "run_id", "eod_signal_id", name="uq_backtest_trade_run_signal"
        ),
        {"extend_existing": True},
    )
