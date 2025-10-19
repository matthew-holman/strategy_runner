from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.handlers.security import SecurityHandler
from app.models.security import SecurityRead
from app.utils import Log

INTERFACE = "securities"

router = APIRouter(
    prefix=f"/{INTERFACE}",
    tags=[INTERFACE.capitalize()],
    responses={
        400: {"detail": "Error details"},
        401: {"detail": "Access token was not provided"},
        403: {"detail": "Not authenticated"},
        404: {"detail": "Error details"},
    },
)


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[SecurityRead])
def list_securities(
    ids: Optional[List[int]] = Query(default=None, alias="ids"),
    db_session: Session = Depends(get_db),
):
    handler = SecurityHandler(db_session)

    if ids:
        securities = handler.get_by_ids(ids)
        Log.info(f"Fetched {len(securities)} securities for IDs {ids}")
        return securities

    securities = handler.get_all()
    Log.info(f"Fetched {len(securities)} total securities")
    return securities


@router.get(
    "/{security_id}", status_code=status.HTTP_200_OK, response_model=SecurityRead
)
def get_security(security_id: int, db_session: Session = Depends(get_db)):
    security = SecurityHandler(db_session).get_by_id(security_id)
    if not security:
        Log.info(f"No security found for id {security_id}")
        return None
    return security
