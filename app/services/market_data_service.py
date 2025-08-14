from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, TypedDict

import pandas as pd
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

    @staticmethod
    def fetch_daily_open_for_ticker(
        security_symbol: str, on_date: date
    ) -> Optional[float]:
        """
        Return the 'open' used for validation on `on_date`, or None if no bar is available
        (holiday, bad ticker, provider lag).
        Reuses fetch_ohlcv_history to keep normalization in one place.
        """
        # yfinance daily bars: safer to use [on_date, on_date+1) so the row is included
        rows = MarketDataService.fetch_ohlcv_history(
            ticker=security_symbol,
            start_date=on_date,
            end_date=on_date + timedelta(days=1),
            interval="1d",
        )
        if not rows:
            return None

        # There *should* be one row with 'date' == on_date (ISO string or datetime depending on your normalization)
        # Your fetch_ohlcv_history resets index to a 'date' column (Python date if source tz plays nice),
        # but be defensive:
        for r in rows:
            r_date = r.get("date")
            if isinstance(r_date, date):
                if r_date == on_date:
                    return float(r["open"])
            else:
                # r_date may be a datetime or ISO string -> normalize and compare
                try:
                    d = date.fromisoformat(str(r_date)[:10])
                    if d == on_date:
                        return float(r["open"])
                except Exception as e:
                    Log.warning(f"Failed to fetch open for {security_symbol}: {e}")
                    continue

        return None

    @staticmethod
    def fetch_early_volume_5m(security_symbol: str, on_date: date) -> int | None:
        df = yf.Ticker(security_symbol).history(
            start=on_date.isoformat(),
            end=(on_date + timedelta(days=1)).isoformat(),
            interval="5m",
            auto_adjust=False,
        )
        if df.empty:
            return None

        # Convert to ET and take the first regular-session bar (09:30–09:35)
        df = df.tz_convert("America/New_York")
        mask = (df.index.time >= time(9, 30)) & (df.index.time < time(9, 35))
        first_bar = df.loc[mask]
        if first_bar.empty:
            return None

        vol = first_bar["Volume"].iloc[0]
        return int(vol) if pd.notna(vol) else None

    @staticmethod
    def fetch_early_volumes_5m(
        security_symbols: List[str], on_date: date
    ) -> Dict[str, int | None]:
        """
        Fetch early volumes for multiple tickers at the 09:30–09:35 ET bar.
        Returns a dict {ticker: early_volume or None}.
        """
        out: Dict[str, int | None] = {}
        for security_symbol in security_symbols:
            try:
                out[security_symbol] = MarketDataService.fetch_early_volume_5m(
                    security_symbol, on_date
                )
            except Exception as e:
                Log.warning(f"Failed to fetch 5m open for {security_symbol}: {e}")
                out[security_symbol] = None
        return out
