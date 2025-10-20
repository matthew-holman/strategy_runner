from typing import Dict, Optional

from pydantic import BaseModel, Field


class MetricResult(BaseModel):
    value: Optional[float] = Field(None, description="Raw numeric value of the metric")
    passed: Optional[bool] = Field(
        None, description="Whether the metric met the target threshold"
    )


class FinancialHealth(BaseModel):
    # --- Core Identifiers ---
    ticker: str = Field(..., description="Ticker symbol, e.g. AAPL")
    company_name: Optional[str] = Field(None, description="Full company name")
    sector: Optional[str] = Field(None, description="Industry sector classification")
    market_cap: Optional[float] = Field(
        None, description="Market capitalization in USD"
    )

    # --- Derived Scoring ---
    financial_score: int = Field(..., description="Composite score from 0–6")
    grade: str = Field(
        ..., description="Letter grade: A (strong), B (moderate), C (weak)"
    )

    # --- Scoring Metrics ---
    metrics: Dict[str, MetricResult] = Field(
        ..., description="Each metric’s value and pass/fail result"
    )

    # --- Raw Financial Data (context) ---
    eps_current: Optional[float] = Field(None, description="Trailing EPS")
    eps_previous: Optional[float] = Field(
        None, description="Forward or prior-year EPS used for growth calculation"
    )
    revenue_growth_yoy: Optional[float] = Field(
        None, description="Year-over-year revenue growth"
    )
    debt_to_equity: Optional[float] = Field(None, description="Debt-to-equity ratio")
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow in USD")
    institutional_ownership: Optional[float] = Field(
        None, description="Fraction of shares held by institutions"
    )
    pe_ratio: Optional[float] = Field(None, description="Trailing P/E ratio")
