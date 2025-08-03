from datetime import date, datetime, timezone
from typing import Dict, List, Optional, TypedDict

import yfinance as yf

from app.utils import Log


class TickerMetadata(TypedDict):
    first_trade_date: Optional[date]
    exchange: Optional[str]


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

    @staticmethod
    def fetch_ticker_metadata(security_symbol: str) -> TickerMetadata:
        try:
            yf_ticker = yf.Ticker(security_symbol)
            info = yf_ticker.info  # This triggers an API call

            # Parse first trade date
            ms = info.get("firstTradeDateMilliseconds")
            first_trade_date = (
                datetime.fromtimestamp(ms / 1000, timezone.utc).date()
                if ms is not None
                else None
            )

            # Get exchange
            exchange = info.get("fullExchangeName") or info.get("exchange")

            return {
                "first_trade_date": first_trade_date,
                "exchange": exchange,
            }

        except Exception as e:
            Log.warning(f"Failed to fetch metadata for {security_symbol}: {e}")
            return {
                "first_trade_date": None,
                "exchange": None,
            }
