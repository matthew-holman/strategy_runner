from datetime import date

from sqlmodel import Field

from app.models.base_model import BaseModel


class IndexConstituent(BaseModel, table=True):  # type: ignore[call-arg]
    SP500: str = "S&P 500"

    index_name: str = Field(default=SP500, index=True)
    snapshot_date: date = Field(
        index=True
    )  # date when the snapshot was taken (i.e., detected change)
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
    snapshot_hash: str = Field(index=True)

    class Config:
        table = True
