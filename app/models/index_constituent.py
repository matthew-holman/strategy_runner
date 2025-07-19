from datetime import date
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base_model import BaseModel

SP500: str = "S&P 500"


class IndexConstituentBase(BaseModel, table=False):  # type: ignore[call-arg]

    index_name: str = Field(default=SP500, index=True)
    snapshot_date: date = Field(
        index=True,
        description="As historic data is added this represents when this version of the index was actual",
    )
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
        index=True,
        description="The Central Index Key (CIK) used by the SEC to uniquely identify corporations and individuals",
    )


class IndexConstituent(IndexConstituentBase, table=True):  # type: ignore[call-arg]

    __tablename__ = "index_constituent"

    id: int = Field(default=None, primary_key=True)

    __table_args__ = (
        UniqueConstraint(
            "index_name", "symbol", "snapshot_date", name="uq_index_constituent_daily"
        ),
    )


class IndexConstituentCreate(IndexConstituentBase):
    pass


class IndexConstituentRead(IndexConstituentBase):
    id: int


class IndexSnapshot(BaseModel, table=True):  # type: ignore[call-arg]

    __tablename__ = "index_snapshot"

    id: Optional[int] = Field(default=None, primary_key=True)
    index_name: str = Field(index=True)
    snapshot_hash: str = Field(index=False)
    snapshot_date: date = Field(
        index=True,
        description="As historic data is added this represents when this version of the index was actual",
    )
