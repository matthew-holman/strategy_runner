from typing import Optional

import yfinance as yf

from app.models.financial_health import FinancialHealth


class FinancialHealthService:
    TARGETS = {
        "eps_growth_yoy": 0.25,
        "revenue_growth_yoy": 0.20,
        "debt_to_equity": 0.5,
        "free_cash_flow": 0.0,
        "institutional_ownership": 0.5,
        "pe_ratio": 40,
    }

    @classmethod
    def fetch_financial_data(cls, ticker: str) -> Optional[FinancialHealth]:
        try:
            ticker_data = yf.Ticker(ticker)
            info = ticker_data.info
        except Exception:
            return None

        if not info or "longName" not in info:
            return None

        eps_current = info.get("trailingEps")
        eps_previous = info.get("forwardEps")  # fallback proxy
        eps_growth_yoy = None
        if eps_current and eps_previous and eps_previous != 0:
            eps_growth_yoy = (eps_current - eps_previous) / abs(eps_previous)

        # ---- Context-aware targets ----
        sector = info.get("sector", "")
        debt_limit = cls.TARGETS["debt_to_equity"]
        if "Financial" in sector:
            debt_limit = 10.0
        elif "Real Estate" in sector:
            debt_limit = 2.0

        # ---- Growth-adjusted P/E logic ----
        pe = info.get("trailingPE")
        pe_passed = False
        if pe and eps_growth_yoy and eps_growth_yoy > 0:
            peg = pe / (eps_growth_yoy * 100)
            pe_passed = peg < 1.5
        elif pe and pe < cls.TARGETS["pe_ratio"]:
            pe_passed = True

        # ---- FCF rule (allow negatives for hyper-growers) ----
        fcf = info.get("freeCashflow")
        fcf_passed = fcf is not None and (
            fcf > 0 or (eps_growth_yoy and eps_growth_yoy > 0.5)
        )

        # ---- Metric evaluations ----
        metrics = {
            "eps_growth_yoy": {
                "value": eps_growth_yoy,
                "passed": eps_growth_yoy is not None
                and eps_growth_yoy >= cls.TARGETS["eps_growth_yoy"],
            },
            "revenue_growth_yoy": {
                "value": info.get("revenueGrowth"),
                "passed": info.get("revenueGrowth") is not None
                and info["revenueGrowth"] >= cls.TARGETS["revenue_growth_yoy"],
            },
            "debt_to_equity": {
                "value": info.get("debtToEquity"),
                "passed": info.get("debtToEquity") is not None
                and info["debtToEquity"] < debt_limit,
            },
            "free_cash_flow": {
                "value": fcf,
                "passed": fcf_passed,
            },
            "institutional_ownership": {
                "value": info.get("heldPercentInstitutions"),
                "passed": info.get("heldPercentInstitutions") is not None
                and info["heldPercentInstitutions"]
                > cls.TARGETS["institutional_ownership"],
            },
            "pe_ratio": {
                "value": pe,
                "passed": pe_passed,
            },
        }

        # ---- Score, penalty, and grading ----
        score = sum(1 for m in metrics.values() if m["passed"])
        missing_penalty = sum(1 for m in metrics.values() if m["value"] is None)
        score = max(score - (missing_penalty // 2), 0)

        grade = cls._grade(score)

        return FinancialHealth(
            ticker=ticker.upper(),
            company_name=info.get("longName"),
            sector=sector,
            market_cap=info.get("marketCap"),
            financial_score=score,
            grade=grade,
            metrics=metrics,
            eps_current=eps_current,
            eps_previous=eps_previous,
            revenue_growth_yoy=info.get("revenueGrowth"),
            debt_to_equity=info.get("debtToEquity"),
            free_cash_flow=fcf,
            institutional_ownership=info.get("heldPercentInstitutions"),
            pe_ratio=pe,
        )

    @staticmethod
    def _grade(score: int) -> str:
        if score >= 5:
            return "A"
        elif score == 4:
            return "B+"
        elif score == 3:
            return "B"
        return "C"
