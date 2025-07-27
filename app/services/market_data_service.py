from datetime import date
from typing import Dict, List, Optional

import yfinance as yf

from app.utils import Log


class MarketDataService:

    @staticmethod
    def fetch_ohlcv_history(
        ticker: str,
        start_date: date,
        end_date: Optional[date] = None,
        interval: str = "1d",
    ) -> List[Dict] | None:

        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(
                start=start_date.isoformat(),
                end=end_date.isoformat() if end_date else None,
                interval=interval,
                auto_adjust=False,
            )
        except Exception as e:
            Log.error(f"Error fetching {ticker} from Yahoo Finance: {e}")
            raise e

        if df.empty:
            return None

        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Adj Close": "adjusted_close",
            }
        )

        df = df[["open", "high", "low", "close", "adjusted_close", "volume"]]
        df.index.name = "date"
        df.reset_index(inplace=True)

        return df.to_dict(orient="records")
