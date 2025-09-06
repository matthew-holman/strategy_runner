from enum import Enum

from pydantic import BaseModel, Field


class EntryMode(str, Enum):
    IMMEDIATE_AT_OPEN = "IMMEDIATE_AT_OPEN"


class Unit(str, Enum):
    ATR = "atr_14"


class AtrMultiple(BaseModel):
    unit: Unit = Unit.ATR
    multiple: float


class EntryConfig(BaseModel):
    mode: EntryMode = EntryMode.IMMEDIATE_AT_OPEN


class ExitConfig(BaseModel):
    stop_offset: AtrMultiple
    target_offset: AtrMultiple


class ExecutionStrategy(BaseModel):
    version: int = 0
    strategy_id: str
    entry: EntryConfig
    exit: ExitConfig
    max_hold_days: int = Field(ge=1)
