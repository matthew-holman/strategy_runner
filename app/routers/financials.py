from fastapi import APIRouter, HTTPException

from app.models.financial_health import FinancialHealth
from app.services.financial_health_service import FinancialHealthService

INTERFACE = "financials"

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


@router.get("/{ticker}", response_model=FinancialHealth)
def get_financial_health(ticker: str):
    result = FinancialHealthService.fetch_financial_data(ticker)
    if not result:
        raise HTTPException(
            status_code=404, detail="Ticker not found or data unavailable"
        )
    return result
