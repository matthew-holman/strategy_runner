from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel as PydanticBase
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlmodel import Field

from app.models.base_model import BaseModel


class BacktestConfig(PydanticBase):
    fixed_notional_amount: float | None = Field(default=10_000.0, ge=0.0)

    atr_period: int = Field(default=14, ge=2)
    k_stop: float = 1.0
    k_target: float = 2.0
    max_holding_days: int = Field(default=10, ge=1)

    conservative_intra_bar_rule: bool = True
    conservative_gap_rule: bool = True


class BacktestRun(BaseModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "backtest_run"

    __table_args__ = ({"extend_existing": True},)

    run_id: UUID = Field(default_factory=uuid4, primary_key=True)
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    strategy_id: str = Field(index=True)

    # Compact, indexed fingerprint of the config for quick equality/filter joins
    backtest_config_data: dict = Field(
        sa_column=Column(MutableDict.as_mutable(JSONB), nullable=False),
        default_factory=lambda: BacktestConfig().model_dump(mode="json"),
    )

    # ----- Typed accessors ----------------------------------------------------
    def backtest_config(self) -> BacktestConfig:
        """Typed view over the stored JSON."""
        return BacktestConfig.model_validate(self.backtest_config_data)

    def set_backtest_config(self, config: BacktestConfig) -> None:
        """Assign typed config and keep JSON + hash in sync."""
        self.backtest_config_data = config.model_dump(mode="json")
