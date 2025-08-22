from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, TypedDict

import yfinance as yf

from app.utils.log_wrapper import Log


class OHLCV(TypedDict, total=False):
    open: float
    high: float
    low: float
    close: float
    volume: int
    # only present in daily fetch
    date: datetime
    adjusted_close: float


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
    ) -> List[OHLCV]:
        """
        Fetch OHLCV history for a ticker.
        Returns a list of OHLCV (typed) dicts with keys:
        date, open, high, low, close, volume, adjusted_close.
        empty list if no data.
        """

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
            return []

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

        df = df[["open", "high", "low", "close", "volume", "adjusted_close"]]
        df.index.name = "date"
        df.reset_index(inplace=True)

        records: List[OHLCV] = df.to_dict(orient="records")  # type: ignore
        return records

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

    @staticmethod
    def fetch_early_ohlcv_5m(security_symbol: str, on_date: date) -> Optional[OHLCV]:
        """
        Return the first regular-session 5m bar (09:30–09:35 ET) as OHLCV.
        None if unavailable (holiday, no data yet).
        """
        try:
            df = yf.Ticker(security_symbol).history(
                start=on_date.isoformat(),
                end=(on_date + timedelta(days=1)).isoformat(),
                interval="5m",
                auto_adjust=False,
            )
        except Exception as e:
            Log.warning(f"Failed to fetch 5m history for {security_symbol}: {e}")
            return None

        if df.empty:
            return None

        # Convert to ET and select the first regular-session bar
        df = df.tz_convert("America/New_York")
        mask = (df.index.time >= time(9, 30)) & (df.index.time < time(9, 35))
        first_bar = df.loc[mask]
        if first_bar.empty:
            return None

        row = first_bar.iloc[0]

        return OHLCV(
            open=float(row.get("Open")),
            high=float(row.get("High")),
            low=float(row.get("Low")),
            close=float(row.get("Close")),
            volume=int(row.get("Volume")),
        )

    @staticmethod
    def fetch_early_ohlcvs_5m(
        security_symbols: List[str], on_date: date
    ) -> Dict[str, Optional[OHLCV]]:
        """
        Batch wrapper over fetch_early_ohlcv_5m. Returns {symbol: EarlyBar|None}.
        """
        out: Dict[str, Optional[OHLCV]] = {}
        for sym in security_symbols:
            try:
                out[sym] = MarketDataService.fetch_early_ohlcv_5m(sym, on_date)
            except Exception as e:
                Log.warning(f"Failed to fetch 5m early bar for {sym}: {e}")
                out[sym] = None
        return out
