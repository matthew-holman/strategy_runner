import hashlib

from datetime import date
from typing import Optional, Set

from sqlmodel import Field, Relationship

from app.models.base_model import BaseModel


class StockIndexSnapshot(BaseModel, table=True):  # type: ignore[call-arg]

    __tablename__ = "stock_index_snapshot"

    id: Optional[int] = Field(default=None, primary_key=True)
    index_name: str = Field(index=True)
    snapshot_hash: str = Field(index=False)
    snapshot_date: date = Field(
        index=True,
        description="As historic data is added this represents when this version of the index was actual",
    )
    constituents: list["StockIndexConstituent"] = Relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="snapshot"
    )

    @staticmethod
    def compute_snapshot_hash(symbols: Set[str]) -> str:
        canonical = ",".join(sorted(symbols))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


StockIndexSnapshot.model_rebuild()
