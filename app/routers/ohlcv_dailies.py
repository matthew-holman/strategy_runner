from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.handlers.ohlcv_daily import OHLCVDailyHandler
from app.models.ohlcv_daily import OHLCVDailyRead
from app.utils import Log

INTERFACE = "ohlcv_daylies"

router = APIRouter(
    prefix=f"/{INTERFACE}",
    tags=[INTERFACE.upper()],
    responses={
        400: {"detail": "Error details"},
        401: {"detail": "Access token was not provided"},
        403: {"detail": "Not authenticated"},
        404: {"detail": "Error details"},
    },
)


@router.get(
    "/{security_id}",
    status_code=status.HTTP_200_OK,
    response_model=List[OHLCVDailyRead],
)
def list_candles(
    security_id: int,
    from_date: date = Query(default=date.today(), alias="from"),
    to_date: date = Query(default=date.today(), alias="to"),
    db_session: Session = Depends(get_db),
):
    candles = OHLCVDailyHandler(db_session).get_period_for_security(
        from_date, to_date, security_id
    )

    if not candles:
        Log.info(
            f"No OHLCV data found for security {security_id} in range {from_date}..{to_date}"
        )
        return []

    return candles
