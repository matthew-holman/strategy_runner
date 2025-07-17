from datetime import datetime, timezone

from pydantic import Extra
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


def to_camel(string: str) -> str:
    split_string = string.split("_")
    return split_string[0] + "".join(word.capitalize() for word in split_string[1:])


def default_now() -> datetime:
    """Default value for created_at and updated_at columns."""
    return datetime.now(timezone.utc)


class BaseModel(SQLModel):
    __abstract__ = True

    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )

    # deleted_at: datetime | None = Field(
    #     default=None,
    #     sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    # )
    #
    # deleted: bool = Field(default=False)
    #
    # def delete(self):
    #     self.deleted = True
    #     self.deleted_at = datetime.now(timezone.utc)

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        extra = Extra.ignore
