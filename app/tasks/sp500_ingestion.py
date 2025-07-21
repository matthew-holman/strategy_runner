import hashlib
import time

from datetime import date, datetime
from typing import Dict, List, Set

from core.db import get_db
from handlers.index_constituent import IndexConstituentHandler
from handlers.security import SecurityHandler
from models.index_constituent import SP500, IndexConstituentCreate
from requests import HTTPError

from app.services.wiki_scraper import (
    WIKI_PAGE,
    fetch_html,
    get_wayback_snapshot_list,
    parse_sp500_constituents_html,
)
from app.utils import Log


def daily_sp500_sync():
    html = fetch_html(WIKI_PAGE)
    records = parse_sp500_constituents_html(html)
    Log.info(f"{len(records)} records parsed from S&P 500 Wikipedia page.")

    symbols = {r["symbol"].strip().upper() for r in records}
    snapshot_hash = compute_snapshot_hash(symbols)
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
    snapshot_urls = get_wayback_snapshot_list()

    with next(get_db()) as db_session:
        ic_handler = IndexConstituentHandler(db_session)
        security_handler = SecurityHandler(db_session)

        oldest_hash = ic_handler.get_earliest_snapshot(SP500).snapshot_hash
        oldest_snapshot_date = ic_handler.get_earliest_snapshot(SP500).snapshot_date

        # Iterate backwards through snapshots (most recent to oldest)
        for snapshot in snapshot_urls[-2::-1]:
            snapshot_date = datetime.strptime(snapshot[0], "%Y%m%d%H%M%S").date()
            if snapshot_date > oldest_snapshot_date:
                Log.info(
                    f"Skipping snapshot from {snapshot_date}, newer than DB's oldest snapshot."
                )
                continue

            time.sleep(10)  # be kind to way back machine

            try:
                wayback_snapshot_url = (
                    f"https://web.archive.org/web/{snapshot[0]}/{snapshot[1]}"
                )
                html = fetch_html(wayback_snapshot_url)
            except HTTPError as err:
                Log.error(
                    f"Got HTTP error {err.response} in response when requesting page for {snapshot[0]}"
                )
                continue

            records = parse_sp500_constituents_html(html)
            symbols = {r["symbol"].strip().upper() for r in records}
            snapshot_hash = compute_snapshot_hash(symbols)

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


def compute_snapshot_hash(symbols: Set[str]) -> str:
    canonical = ",".join(sorted(symbols))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def map_ic_objects(
    records: List[Dict],
    security_handler: SecurityHandler,
    snapshot_id: int,
):
    ic_objects = []
    for record in records:
        security = security_handler.get_or_create(record)
        ic_objects.append(
            IndexConstituentCreate(
                index_name=SP500,
                snapshot_id=snapshot_id,
                security_id=security.id,
            )
        )
    return ic_objects
