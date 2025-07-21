from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base_model import BaseModel

SP500: str = "S&P 500"


class IndexConstituentBase(BaseModel, table=False):  # type: ignore[call-arg]

    index_name: str = Field(default=SP500, index=True)
    security_id: int = Field(foreign_key="security.id")
    snapshot_id: int = Field(foreign_key="index_snapshot.id")
    # snapshot: Optional[IndexSnapshot] = Relationship(back_populates="constituents")


class IndexConstituent(IndexConstituentBase, table=True):  # type: ignore[call-arg]

    __tablename__ = "index_constituent"

    id: int = Field(default=None, primary_key=True)

    __table_args__ = (
        UniqueConstraint(
            "snapshot_id", "security_id", name="uq_constituent_snapshot_security"
        ),
    )


class IndexConstituentCreate(IndexConstituentBase):
    pass


class IndexConstituentRead(IndexConstituentBase):
    id: int


IndexConstituent.model_rebuild()
