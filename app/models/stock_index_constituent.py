from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from app.models.base_model import BaseModel
from app.models.security import Security
from app.models.stock_index_snapshot import StockIndexSnapshot

SP500: str = "S&P 500"


class StockIndexConstituentBase(BaseModel, table=False):  # type: ignore[call-arg]

    index_name: str = Field(default=SP500, index=True)
    security_id: int = Field(foreign_key="security.id")
    snapshot_id: int = Field(foreign_key="stock_index_snapshot.id")


class StockIndexConstituent(StockIndexConstituentBase, table=True):  # type: ignore[call-arg]

    __tablename__ = "stock_index_constituent"

    id: int = Field(default=None, primary_key=True)

    __table_args__ = (
        UniqueConstraint(
            "snapshot_id", "security_id", name="uq_constituent_snapshot_security"
        ),
        {"extend_existing": True},
    )

    snapshot: Optional[StockIndexSnapshot] = Relationship(back_populates="constituents")
    security: Optional[Security] = Relationship(back_populates="constituents")


class StockIndexConstituentCreate(StockIndexConstituentBase):
    pass


class StockIndexConstituentRead(StockIndexConstituentBase):
    id: int


StockIndexConstituent.model_rebuild()
