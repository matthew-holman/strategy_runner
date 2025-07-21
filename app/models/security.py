from sqlmodel import Field

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


class Security(SecurityBase, table=True):  # type: ignore[call-arg]

    id: int = Field(default=None, primary_key=True)


class SecurityCreate(SecurityBase):  # type: ignore[call-arg]
    pass


class SecurityRead(SecurityBase):  # type: ignore[call-arg]
    id: int


Security.model_rebuild()
