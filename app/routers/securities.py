from fastapi import APIRouter, Depends, status
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


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[SecurityRead])
def list_securities(db_session: Session = Depends(get_db)):
    securities = SecurityHandler(db_session).get_all()
    if not securities:
        Log.info("No securities found")
        return []
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
