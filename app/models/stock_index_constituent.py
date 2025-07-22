from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base_model import BaseModel

SP500: str = "S&P 500"


class StockIndexConstituentBase(BaseModel, table=False):  # type: ignore[call-arg]

    index_name: str = Field(default=SP500, index=True)
    security_id: int = Field(foreign_key="security.id")
    snapshot_id: int = Field(foreign_key="stock_index_snapshot.id")
    # snapshot: Optional[IndexSnapshot] = Relationship(back_populates="constituents")


class StockIndexConstituent(StockIndexConstituentBase, table=True):  # type: ignore[call-arg]

    __tablename__ = "stock_index_constituent"

    id: int = Field(default=None, primary_key=True)

    __table_args__ = (
        UniqueConstraint(
            "snapshot_id", "security_id", name="uq_constituent_snapshot_security"
        ),
    )


class StockIndexConstituentCreate(StockIndexConstituentBase):
    pass


class StockIndexConstituentRead(StockIndexConstituentBase):
    id: int


StockIndexConstituent.model_rebuild()
