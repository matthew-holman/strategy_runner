import datetime

from typing import Any, Generator, List, Optional, Set

from core.orm_mixins import ColumnMappingMixIn
from sqlalchemy import MetaData, create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.declarative import declarative_base
from sqlmodel import Session

from app.core.settings import get_settings

settings = get_settings()

engine = create_engine(
    url=(
        f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    ),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)


def get_db() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


Base = declarative_base(
    metadata=MetaData(),
    cls=(ColumnMappingMixIn,),
)


def upsert(
    model: Any,
    db_session: Session,
    constraint: Optional[str],
    data_iter: List[Any],
    exclude_columns: Set[str],
) -> List[Any]:
    data = [row.dict(exclude=exclude_columns) for row in data_iter]
    insert_statement = insert(model.__table__).values(data)
    updated_params = {
        c.key: c for c in insert_statement.excluded if c.key not in exclude_columns
    }
    updated_params["updated_at"] = datetime.datetime.now(datetime.UTC)  # type: ignore
    upsert_statement = insert_statement.on_conflict_do_update(
        constraint=constraint,
        set_=updated_params,
    ).returning(model.__table__)
    updated_objects = db_session.execute(upsert_statement).fetchall()
    return [model(**row) for row in updated_objects]
