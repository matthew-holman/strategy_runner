from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EntryMode(str, Enum):
    IMMEDIATE_AT_OPEN = "IMMEDIATE_AT_OPEN"
    PERCENT_UNDER_OPEN = "PERCENT_UNDER_OPEN"


class Unit(str, Enum):
    ATR = "atr_14"


class AtrMultiple(BaseModel):
    unit: Unit = Unit.ATR
    multiple: float


class EntryConfig(BaseModel):
    mode: EntryMode = EntryMode.IMMEDIATE_AT_OPEN
    percent_below_open: Optional[float] = Field(
        default=None, description="e.g. 0.01 for 1% under the bar's open"
    )
    valid_for_bars: Optional[int] = Field(
        default=None, ge=1, description="Buy window (bars) from the start bar"
    )


class ExitConfig(BaseModel):
    stop_offset: AtrMultiple
    target_offset: AtrMultiple


class ExecutionStrategy(BaseModel):
    version: int = 0
    strategy_id: str
    entry: EntryConfig
    exit: ExitConfig
    max_hold_days: int = Field(ge=1)
    active: bool = False
