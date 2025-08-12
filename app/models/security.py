from datetime import date
from typing import Optional

from sqlmodel import Field, Relationship

from app.models.base_model import BaseModel


class SecurityBase(BaseModel, table=False):  # type: ignore[call-arg]
    symbol: str = Field(
        index=True, description="The stock ticker symbol as of the snapshot date"
    )
    company_name: str
    gics_sector: str = Field(
        description="The Global Industry Classification Standard (GICS) sector for the company"
    )
    gics_sub_industry: str = Field(
        description="The GICS sub-industry classification within the sector"
    )
    cik: str = Field(
        default=None,
        nullable=True,
        index=True,
        description="The Central Index Key (CIK) used by the SEC to uniquely identify corporations and individuals",
    )

    first_trade_date: Optional[date] = (
        None  # Based on yahoo ticker.info() firstTradeDateMilliseconds
    )
    exchange: Optional[str] = None  # Based on yahoo ticker.info()`fullExchangeName`


class Security(SecurityBase, table=True):  # type: ignore[call-arg]

    id: int = Field(default=None, primary_key=True)
    constituents: list["StockIndexConstituent"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="security"
    )


class SecurityCreate(SecurityBase):  # type: ignore[call-arg]
    pass


class SecurityRead(SecurityBase):  # type: ignore[call-arg]
    id: int


Security.model_rebuild()
