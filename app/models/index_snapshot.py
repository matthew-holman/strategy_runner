from datetime import date
from typing import Optional

from sqlmodel import Field

from app.models.base_model import BaseModel


class IndexSnapshot(BaseModel, table=True):  # type: ignore[call-arg]

    __tablename__ = "index_snapshot"

    id: Optional[int] = Field(default=None, primary_key=True)
    index_name: str = Field(index=True)
    snapshot_hash: str = Field(index=False)
    snapshot_date: date = Field(
        index=True,
        description="As historic data is added this represents when this version of the index was actual",
    )
    # constituents: list["IndexConstituent"] = Relationship(back_populates="snapshot")


IndexSnapshot.model_rebuild()
