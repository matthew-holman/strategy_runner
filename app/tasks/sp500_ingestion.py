import time

from datetime import date, datetime
from typing import Dict, List

from core.db import get_db
from handlers.index_constituent import IndexConstituentHandler
from handlers.security import SecurityHandler
from models.stock_index_constituent import SP500, StockIndexConstituentCreate
from models.stock_index_snapshot import StockIndexSnapshot
from requests import HTTPError

from app.services.stock_index_service import (
    extract_constituents,
    get_latest_snapshot_html,
    get_snapshot_html_from_wayback,
    get_snapshot_timestamps,
)
from app.utils import Log


def daily_sp500_sync():
    html = get_latest_snapshot_html()
    records = extract_constituents(html)
    Log.info(f"{len(records)} records parsed from S&P 500 Wikipedia page.")

    symbols = {r["symbol"].strip().upper() for r in records}
    snapshot_hash = StockIndexSnapshot.compute_snapshot_hash(symbols)
    today = date.today()

    with next(get_db()) as db_session:
        ic_handler = IndexConstituentHandler(db_session)
        security_handler = SecurityHandler(db_session)

        if ic_handler.snapshot_matches_most_recent(SP500, snapshot_hash):
            Log.info("No changes detected in S&P 500 constituents — skipping insert.")
            return

        snapshot = ic_handler.save_snapshot(SP500, snapshot_hash, today)

        ic_objects = map_ic_objects(records, security_handler, snapshot.id)
        ic_handler.save_all(ic_objects)

        db_session.commit()
        Log.info(
            f"{len(ic_objects)} records inserted for {today} with hash {snapshot_hash}"
        )


def backfill_sp500_from_wayback():
    snapshot_urls = get_snapshot_timestamps()

    with next(get_db()) as db_session:
        ic_handler = IndexConstituentHandler(db_session)
        security_handler = SecurityHandler(db_session)

        oldest_snapshot = ic_handler.get_earliest_snapshot(SP500)
        oldest_hash = oldest_snapshot.snapshot_hash
        oldest_snapshot_date = oldest_snapshot.snapshot_date

        for timestamp, original_path in reversed(snapshot_urls[:-1]):
            snapshot_date = datetime.strptime(timestamp, "%Y%m%d%H%M%S").date()
            if snapshot_date > oldest_snapshot_date:
                Log.info(
                    f"Skipping snapshot from {snapshot_date}, newer than DB's oldest snapshot."
                )
                continue

            time.sleep(10)

            try:
                html = get_snapshot_html_from_wayback(timestamp, original_path)
            except HTTPError as err:
                Log.error(
                    f"Got HTTP error {err.response} in response when requesting page for {timestamp}"
                )
                continue

            records = extract_constituents(html)
            symbols = {r["symbol"].strip().upper() for r in records}
            snapshot_hash = StockIndexSnapshot.compute_snapshot_hash(symbols)

            if snapshot_hash == oldest_hash:
                Log.info(
                    f"No changes detected for {snapshot_date} in S&P 500 constituents — skipping insert."
                )
                continue

            snapshot = ic_handler.save_snapshot(SP500, snapshot_hash, snapshot_date)
            ic_objects = map_ic_objects(records, security_handler, snapshot.id)

            ic_handler.save_all(ic_objects)
            db_session.commit()
            Log.info(
                f"{len(ic_objects)} records inserted for {snapshot_date} with hash {snapshot_hash}"
            )

            oldest_hash = snapshot_hash


def map_ic_objects(
    records: List[Dict],
    security_handler: SecurityHandler,
    snapshot_id: int,
) -> List[StockIndexConstituentCreate]:
    ic_objects = []
    for record in records:
        security = security_handler.get_or_create(record)
        ic_objects.append(
            StockIndexConstituentCreate(
                index_name=SP500,
                snapshot_id=snapshot_id,
                security_id=security.id,
            )
        )
    return ic_objects
