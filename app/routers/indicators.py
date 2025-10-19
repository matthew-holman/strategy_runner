from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.handlers.technical_indicator import TechnicalIndicatorHandler
from app.models.technical_indicator import TechnicalIndicatorRead
from app.utils import Log

INTERFACE = "indicators"

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


@router.get(
    "/{security_id}",
    status_code=status.HTTP_200_OK,
    response_model=List[TechnicalIndicatorRead],
)
def list_indicators(
    security_id: int,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    fields: Optional[List[str]] = Query(None),
    db_session: Session = Depends(get_db),
):
    indicators = TechnicalIndicatorHandler(
        db_session
    ).get_selected_fields_for_security_between_dates(
        security_id, from_date, to_date, fields
    )

    if not indicators:
        Log.info(
            f"No indicators found for security {security_id} in range {from_date}..{to_date}"
        )
        return []

    return indicators
