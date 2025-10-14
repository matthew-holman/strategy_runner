import time

from datetime import date, timedelta
from decimal import Decimal
from typing import List

from sqlmodel import Session

from app.core.db import get_db
from app.handlers.ohlcv_daily import OHLCVDailyHandler
from app.handlers.security import SecurityHandler
from app.handlers.stock_index_constituent import StockIndexConstituentHandler
from app.indicators.compute import TRADING_DAYS_REQUIRED
from app.models.ohlcv_daily import OHLCVDailyCreate
from app.models.security import Security
from app.models.stock_index_constituent import SP500
from app.services.market_data_service import OHLCV, MarketDataService
from app.utils.datetime_utils import chunk_date_range, last_year, yesterday
from app.utils.log_wrapper import Log
from app.utils.trading_calendar import (
    get_all_trading_days_between,
    get_nth_trading_day,
)


def daily_candle_fetch():
    with next(get_db()) as db_session:
        stock_ic_handler = StockIndexConstituentHandler(db_session)
        latest_sp500_snapshot = stock_ic_handler.get_most_recent_snapshot(SP500)

        index_constituents = stock_ic_handler.get_by_snapshot_id(
            latest_sp500_snapshot.id
        )

        ohlcv_handler = OHLCVDailyHandler(db_session)
        today = date.today()

        for index_constituent in index_constituents:
            from_date = (
                ohlcv_handler.get_latest_candle_date(index_constituent.security.id)
                or yesterday()
            )
            if from_date >= today:
                Log.info(
                    f"No new data to fetch for {index_constituent.security.symbol} — up to date."
                )
                continue

            records = MarketDataService.fetch_ohlcv_history(
                index_constituent.security.symbol, from_date, today
            )

            if records:
                daily_candles = _map_ohlcv_objects(
                    records, index_constituent.security.id
                )
                ohlcv_handler.save_all(daily_candles)
                db_session.commit()
                Log.info(
                    f"Inserted {len(daily_candles)} daily OHLCV records for security "
                    f"{index_constituent.security.company_name} from {from_date} to today"
                )


def heal_missing_candle_data() -> None:
    """
    Identify and backfill missing OHLCV data per security by comparing against expected trading days.
    """
    with next(get_db()) as db_session:
        security_handler = SecurityHandler(db_session)

        all_securities = security_handler.get_all()

        for security in all_securities:
            try:
                if security.exchange is None or security.first_trade_date is None:
                    Log.warning(f"skipping {security.symbol} missing metadata.")
                    continue

                oldest_required_candle_date = get_nth_trading_day(
                    exchange=security.exchange,
                    as_of=last_year(),
                    offset=-abs(TRADING_DAYS_REQUIRED),
                )

                period_start = (
                    oldest_required_candle_date
                    if oldest_required_candle_date > security.first_trade_date
                    else security.first_trade_date
                )

                # find gaps in the data
                missing_dates = _find_missing_trading_days(
                    security_id=security.id,
                    exchange=security.exchange,
                    start_date=period_start,
                    end_date=yesterday(),
                    session=db_session,
                )

                if not missing_dates:
                    Log.info(f"No gaps found for {security.symbol}")
                    continue

                Log.info(
                    f"Found {len(missing_dates)} missing candles for {security.symbol}"
                    f" between {min(missing_dates)} and {max(missing_dates)}"
                )

                # fill gaps in the data
                _fetch_and_store_ohlcv_for_security(
                    db_session,
                    security,
                    start_date=min(missing_dates),
                    end_date=max(missing_dates),
                )

            except Exception as e:
                Log.error(f"Failed healing {security.symbol}: {e}")


def _find_missing_trading_days(
    security_id: int, exchange: str, start_date: date, end_date: date, session: Session
) -> List[date]:
    """
    Compare trading calendar to existing candles in DB, and return missing trading days.
    """

    # Step 1: Get valid trading days from calendar
    trading_days = set(get_all_trading_days_between(exchange, start_date, end_date))

    # Step 2: Get existing candle dates from DB
    handler = OHLCVDailyHandler(session)
    existing_dates = set(handler.get_dates_for_security(security_id))

    # Step 3: Subtract and return missing ones
    missing_days = sorted(list(trading_days - existing_dates))
    return missing_days


def _map_ohlcv_objects(
    records: List[OHLCV], security_id: int
) -> List[OHLCVDailyCreate]:
    ohlcv_objects = []
    for record in records:
        ohlcv_objects.append(
            OHLCVDailyCreate(
                candle_date=record["date"].date(),
                open=Decimal(str(record["open"])).quantize(Decimal("0.01")),
                high=Decimal(str(record["high"])).quantize(Decimal("0.01")),
                low=Decimal(str(record["low"])).quantize(Decimal("0.01")),
                close=Decimal(str(record["close"])).quantize(Decimal("0.01")),
                adjusted_close=Decimal(str(record["adjusted_close"])).quantize(
                    Decimal("0.01")
                ),
                volume=record["volume"],
                security_id=security_id,
            )
        )
    return ohlcv_objects


def _chunk_date_range(start: date, end: date, chunk_size: timedelta):
    if start == end:
        return [(start, end)]  # handle common single-day case

    chunks = []
    cursor = start
    while cursor < end:
        chunk_end = min(cursor + chunk_size, end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end
    return chunks


def _fetch_and_store_ohlcv_for_security(
    db_session,
    security: Security,
    start_date: date,
    end_date: date,
    chunk_size: timedelta = timedelta(days=365),
):
    ohlcv_handler = OHLCVDailyHandler(db_session)

    for chunk_start, chunk_end in chunk_date_range(start_date, end_date, chunk_size):
        Log.debug(f"Fetching {security.symbol} from {chunk_start} to {chunk_end}")
        time.sleep(2)

        records = MarketDataService.fetch_ohlcv_history(
            security.symbol, chunk_start, chunk_end
        )

        if not records:
            Log.warning(
                f"No data for {security.symbol} from {chunk_start} to {chunk_end}"
            )
            continue

        candles = _map_ohlcv_objects(records, security.id)
        ohlcv_handler.save_all(candles)
        db_session.commit()

        Log.info(
            f"Inserted {len(candles)} records for {security.symbol} from {chunk_start} to {chunk_end}"
        )
