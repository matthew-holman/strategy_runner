from sqlmodel import Field, SQLModel
from datetime import date
from typing import Optional

from app.models.base_model import BaseModel


class IndexConstituent(BaseModel, table=True):

    index_name: str = Field(index=True)
    snapshot_date: date = Field(index=True)  # date when the snapshot was taken (i.e., detected change)
    symbol: str = Field(index=True)
    company_name: str
    gics_sector: str
    gics_sub_industry: str
    cik: Optional[str] = Field(default=None, index=True)
    date_added: Optional[date] = None
    snapshot_hash: str = Field(index=True)

    class Config:
        table = True