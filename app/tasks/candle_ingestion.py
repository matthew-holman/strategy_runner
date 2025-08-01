import time

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from services.missing_ohlcv_data_event_service import MissingOHLCVDataEventService
from sqlmodel import Session

from app.core.db import get_db
from app.handlers.ohlcv_daily import OHLCVDailyHandler
from app.handlers.security import SecurityHandler
from app.handlers.stock_index_constituent import StockIndexConstituentHandler
from app.models.ohlcv_daily import OHLCVDailyCreate
from app.models.security import Security
from app.models.stock_index_constituent import SP500
from app.services.market_data_service import MarketDataService
from app.utils import Log


def daily_candle_fetch():

    with next(get_db()) as db_session:
        stock_ic_handler = StockIndexConstituentHandler(db_session)
        latest_sp500_snapshot = stock_ic_handler.get_most_recent_snapshot(SP500)

        index_constituents = stock_ic_handler.get_by_snapshot_id(
            latest_sp500_snapshot.id
        )

        ohlcv_handler = OHLCVDailyHandler(db_session)
        today = date.today()
        yesterday = today - timedelta(days=1)

        if _is_weekend(yesterday):
            Log.info("Yesterday was a weekend, no data to pull.")
        else:
            for index_constituent in index_constituents:

                from_date = (
                    ohlcv_handler.get_latest_candle_date(index_constituent.security.id)
                    or yesterday
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


def fix_historical_gaps():
    with next(get_db()) as db_session:
        missing_data_event_service = MissingOHLCVDataEventService(db_session)
        for event in missing_data_event_service.get_pending():
            _fetch_history_for_security(
                db_session=db_session,
                security_id=event.security_id,
                start_date=event.start_date,
                end_date=event.end_date,
            )
            missing_data_event_service.mark_handled(event.id)
        db_session.commit()


def historical_candle_backfill():
    with next(get_db()) as db_session:
        ic_handler = StockIndexConstituentHandler(db_session)
        security_handler = SecurityHandler(db_session)
        ohlcv_handler = OHLCVDailyHandler(db_session)

        oldest_snapshot_date = ic_handler.get_earliest_snapshot(SP500).snapshot_date
        today = date.today()

        # TODO, when I include other indexes such as the nasdaq I need to limit this it SP500 related securities
        # TODO: Switch to streaming query (e.g., with yield_per) when the number of securities grows
        all_securities = security_handler.get_all()

        for security in all_securities:
            to_date = ohlcv_handler.get_earliest_candle_date(security.id) or today
            if to_date <= oldest_snapshot_date:
                Log.info(f"Skipping {security.symbol}: already backfilled")
                continue

            Log.info(
                f"Backfilling {security.symbol} from {oldest_snapshot_date} to {to_date}"
            )
            _fetch_and_store_ohlcv_for_security(
                db_session, security, oldest_snapshot_date, to_date
            )


def _fetch_history_for_security(
    db_session: Session,
    security_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    ic_handler = StockIndexConstituentHandler(db_session)
    security_handler = SecurityHandler(db_session)
    ohlcv_handler = OHLCVDailyHandler(db_session)

    security = security_handler.get_by_id(security_id)
    if not security:
        Log.error(f"Security with id={security_id} not found")
        return

    if start_date is None:
        start_date = ic_handler.get_earliest_snapshot(SP500).snapshot_date

    if end_date is None:
        end_date = ohlcv_handler.get_earliest_candle_date(security_id) or date.today()

    if end_date <= start_date:
        Log.info(f"{security.symbol} already fully backfilled.")
        return

    Log.info(f"Fetching {security.symbol} from {start_date} to {end_date}")
    _fetch_and_store_ohlcv_for_security(db_session, security, start_date, end_date)


def _map_ohlcv_objects(records: List[Dict], security_id: int) -> List[OHLCVDailyCreate]:
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
    chunks = []
    cursor = start
    while cursor < end:
        chunk_end = min(cursor + chunk_size, end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end
    return chunks


def _is_weekend(d=date.today()):
    return d.weekday() > 4


def _fetch_and_store_ohlcv_for_security(
    db_session,
    security: Security,
    start_date: date,
    end_date: date,
    chunk_size: timedelta = timedelta(days=365),
):
    ohlcv_handler = OHLCVDailyHandler(db_session)

    for chunk_start, chunk_end in _chunk_date_range(start_date, end_date, chunk_size):
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
