from typing import Any, Generator, List, Optional, Set

from sqlalchemy import MetaData, create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.dml import ReturningInsert
from sqlmodel import Session

from app.core.orm_mixins import ColumnMappingMixIn
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
    exclude_columns: Set[str],
    data_iter: List[Any],
    constraint: Optional[str] = None,
    index_elements: Optional[List[str]] = None,
) -> List[Any]:
    data = [row.model_dump(exclude=exclude_columns) for row in data_iter]
    insert_statement = insert(model.__table__).values(data)
    updated_params = {
        c.key: c for c in insert_statement.excluded if c.key not in exclude_columns
    }

    if constraint:
        conflict_stmt = insert_statement.on_conflict_do_update(
            constraint=constraint,
            set_=updated_params,
        )
    elif index_elements:
        conflict_stmt = insert_statement.on_conflict_do_update(
            index_elements=index_elements,
            set_=updated_params,
        )
    else:
        raise ValueError("Either 'constraint' or 'index_elements' must be provided.")

    upsert_statement: ReturningInsert = conflict_stmt.returning(model.__table__)
    updated_objects = db_session.exec(upsert_statement).fetchall()
    return [model(**row._mapping) for row in updated_objects]
