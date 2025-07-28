from datetime import date
from typing import Optional

from sqlmodel import Field

from app.models.base_model import BaseModel


class TechnicalIndicatorBase(BaseModel, table=False):  # type: ignore[call-arg]
    security_id: int = Field(
        foreign_key="security.id",
        primary_key=True,
    )
    measurement_date: date = Field(
        primary_key=True,
    )

    sma_20: Optional[float] = Field(
        default=None, description="20-day simple moving average of the close price"
    )
    sma_50: Optional[float] = Field(
        default=None, description="50-day simple moving average of the close price"
    )
    sma_200: Optional[float] = Field(
        default=None, description="200-day simple moving average of the close price"
    )

    ema_9: Optional[float] = Field(
        default=None, description="9-day exponential moving average of the close price"
    )
    ema_20: Optional[float] = Field(
        default=None, description="20-day exponential moving average of the close price"
    )

    rsi_14: Optional[float] = Field(
        default=None,
        description="Relative Strength Index computed over a 14-day window",
    )

    high_10d: Optional[float] = Field(
        default=None, description="Highest high over the past 10 trading days"
    )

    low_10d: Optional[float] = Field(
        default=None, description="Lowest low over the past 10 trading days"
    )

    avg_vol_20d: Optional[float] = Field(
        default=None, description="Average trading volume over the past 20 trading days"
    )

    macd: Optional[float] = Field(
        default=None,
        description="Moving Average Convergence Divergence line: 12-day EMA minus 26-day EMA of close prices",
    )
    macd_signal: Optional[float] = Field(
        default=None, description="9-day EMA of the MACD line"
    )
    macd_hist: Optional[float] = Field(
        default=None, description="MACD histogram: MACD line minus signal line"
    )

    atr_14: Optional[float] = Field(
        default=None, description="Average True Range computed over 14 days"
    )

    close_position: Optional[float] = Field(
        default=None,
        description="Normalized close position in daily range: (Close - Low) / (High - Low)",
    )


class TechnicalIndicator(TechnicalIndicatorBase, table=True):  # type: ignore[call-arg]

    __tablename__ = "technical_indicator"


class StockIndexConstituentRead(TechnicalIndicatorBase):  # type: ignore[call-arg]
    pass
