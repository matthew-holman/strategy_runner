from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, TypedDict

import yfinance as yf

from yfinance import EquityQuery

from app.utils.log_wrapper import Log

YF_MAX_PAGE_SIZE = 250  # Yahoo’s limit for screener pagination
US_EQUITY_EXCHANGES = {"NMS", "NYQ", "ASE", "NCM", "NGM"}


class OHLCV(TypedDict, total=False):
    open: float
    high: float
    low: float
    close: float
    volume: int
    # only present in daily fetch
    date: datetime
    adjusted_close: float


@dataclass(frozen=True)
class TickerMetadata:
    symbol: str
    company_name: Optional[str]
    gics_sector: Optional[str]  # Yahoo: 'sector' (not true GICS); treat as provisional
    gics_sub_industry: Optional[
        str
    ]  # Yahoo: 'industry' (not true GICS); treat as provisional
    cik: Optional[str]
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
    def fetch_ticker_metadata(symbol: str) -> TickerMetadata:
        """
        Fetch metadata for a single symbol using yfinance.
        Notes:
        - yfinance 'info' fields are not authoritative GICS. We store them provisionally.
        - Failures return a minimal record; caller decides how to persist.
        """
        try:
            ticker = yf.Ticker(symbol)
            # Prefer .get_info() in newer yfinance; .info still widely used but slower / may warn
            info = ticker.get_info() if hasattr(ticker, "get_info") else ticker.info  # type: ignore[attr-defined]

            first_trade_date: Optional[date] = None
            ms = info.get("firstTradeDateMilliseconds")
            if isinstance(ms, (int, float)):
                first_trade_date = datetime.fromtimestamp(
                    ms / 1000, tz=timezone.utc
                ).date()

            exchange = info.get("fullExchangeName") or info.get("exchange")
            company_name = info.get("longName") or info.get("shortName")
            sector = info.get("sector")  # not true GICS sector
            sub_industry = info.get("industry")  # not true GICS sub-industry
            cik_value = info.get("cik")
            if cik_value is not None:
                cik_value = str(cik_value)

            return TickerMetadata(
                symbol=symbol,
                company_name=company_name,
                gics_sector=sector,
                gics_sub_industry=sub_industry,
                cik=cik_value,
                first_trade_date=first_trade_date,
                exchange=exchange,
            )
        except Exception as exc:
            # Keep it resilient; let caller decide about placeholders/backfill
            from app.utils.log_wrapper import Log

            Log.warning(f"Failed to fetch metadata for {symbol}: {exc}")
            return TickerMetadata(
                symbol=symbol,
                company_name=None,
                gics_sector=None,
                gics_sub_industry=None,
                cik=None,
                first_trade_date=None,
                exchange=None,
            )

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

    def fetch_top_equities_by_region(
        self, region: str = "us", limit: int = 2000
    ) -> List[str]:
        """
        Use yfinance.screener to return top-N U.S. equities by market cap.
        - Paginates with offset/size (max 250 per request).
        - Filters to major U.S. exchanges; excludes OTC/PNK and non-equities.
        - Normalizes class-share tickers (e.g., BRK.B -> BRK-B) for yfinance.
        """
        if limit <= 0:
            return []

        if region == "us":
            exchanges = US_EQUITY_EXCHANGES
        else:
            raise ValueError(f"region {region} not supported.")

        query = EquityQuery(
            "and",
            [
                EquityQuery("eq", ["region", region]),
                EquityQuery("is-in", ["exchange", *sorted(exchanges)]),
                EquityQuery(
                    "gte", ["intradayprice", 1]
                ),  # avoid ill-formed/zero-price quotes
            ],
        )

        tickers: list[str] = []
        offset = 0
        page_size = min(limit, YF_MAX_PAGE_SIZE)

        while len(tickers) < limit:
            response = yf.screen(
                query,
                offset=offset,
                size=page_size,
                sortField="percentchange",
                sortAsc=False,
            )
            quotes = response["quotes"]

            # Defensive post-filter: exchange + quoteType can be leaky in some versions.
            # Keep only EQUITY on our target exchanges, then normalize class-share symbols.
            for q in quotes:
                exchange = q.get("exchange")
                if (
                    q.get("quoteType") != "EQUITY"
                    or exchange not in US_EQUITY_EXCHANGES
                ):
                    continue
                symbol = q.get("symbol")
                if symbol:
                    tickers.append(self._normalize_yahoo_symbol(symbol))

            if len(quotes) < page_size:  # no more pages
                break
            offset += page_size

        # De-duplicate while preserving order, then truncate to limit
        seen: set[str] = set()
        unique: list[str] = []
        for t in tickers:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique[:limit]

    @staticmethod
    def _normalize_yahoo_symbol(symbol: str) -> str:
        # Map dot share-classes to dash (yfinance prefers BRK-B, not BRK.B)
        if "." in symbol:
            head, *rest = symbol.split(".")
            if len(rest) == 1 and len(rest[0]) == 1:
                return f"{head}-{rest[0]}"
        return symbol
