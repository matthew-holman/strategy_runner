from datetime import datetime, timezone
from typing import Optional

from pydantic import Extra
from sqlalchemy import DateTime, func
from sqlmodel import Field, SQLModel


def to_camel(string: str) -> str:
    split_string = string.split("_")
    return split_string[0] + "".join(word.capitalize() for word in split_string[1:])


def default_now() -> datetime:
    """Default value for created_at and updated_at columns."""
    return datetime.now(timezone.utc)


class BaseModel(SQLModel):
    __abstract__ = True

    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now(),
        },
    )

    # deleted_at: Optional[datetime] = Field(
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
