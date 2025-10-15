from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from app.core.db import get_db
from app.handlers.eod_signal import EODSignalHandler
from app.models.eod_signal import EODSignalRead
from app.utils import Log

INTERFACE = "signals"

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


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[EODSignalRead])
def list_signals(
    from_date: date = Query(default=date.today(), alias="from"),
    to_date: date = Query(default=date.today(), alias="to"),
    db_session: Session = Depends(get_db),
):
    signals = EODSignalHandler(db_session).get_all_strategy_between_dates(
        from_date, to_date
    )

    if not signals:
        Log.info(f"No signals found for range {from_date}..{to_date}")
        return []

    return signals
