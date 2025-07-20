import hashlib
import time

from datetime import date, datetime

from core.db import get_db
from handlers.index_constituent import IndexConstituentHandler
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

    symbols = [r["symbol"] for r in records]
    snapshot_hash = compute_snapshot_hash(symbols)
    today = date.today()

    with next(get_db()) as db_session:
        ic_handler = IndexConstituentHandler(db_session)
        if ic_handler.snapshot_matches_most_recent(SP500, snapshot_hash):
            Log.info("No changes detected in S&P 500 constituents — skipping insert.")
            return

        ic_objects = map_to_constituents(records, today, snapshot_hash)

        ic_handler.save_all(ic_objects)
        ic_handler.save_snapshot(SP500, snapshot_hash, today)
        db_session.commit()
        Log.info(
            f"{len(ic_objects)} records inserted for {today} with hash {snapshot_hash}"
        )


def backfill_sp500_from_wayback():
    snapshot_urls = get_wayback_snapshot_list()

    with next(get_db()) as db_session:
        ic_handler = IndexConstituentHandler(db_session)
        oldest_hash = ic_handler.get_earliest_snapshot(SP500).snapshot_hash
        oldest_snapshot_date = ic_handler.get_earliest_snapshot(SP500).snapshot_date
        oldest_snapshot_date = date(2019, 1, 6)

        # List is in ascending chronological order, I want to start at the most recent
        for snapshot in snapshot_urls[-2::-1]:
            snapshot_date = datetime.strptime(snapshot[0], "%Y%m%d%H%M%S").date()
            if snapshot_date > oldest_snapshot_date:
                Log.info(
                    f"Skipping wayback page for {snapshot_date}, more recent than oldest DB version."
                )
                continue

            # be kind to way back machine
            time.sleep(10)

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
            snapshot_hash = compute_snapshot_hash([r["symbol"] for r in records])

            if snapshot_hash == oldest_hash:
                Log.info(
                    f"No changes detected for {snapshot_date} in S&P 500 constituents — skipping insert."
                )
                continue

            ic_objects = map_to_constituents(records, snapshot_date)

            ic_handler.save_all(ic_objects)
            ic_handler.save_snapshot(SP500, snapshot_hash, snapshot_date)
            db_session.commit()
            Log.info(
                f"{len(ic_objects)} records inserted for {snapshot_date} with hash {snapshot_hash}"
            )

            oldest_hash = snapshot_hash


def compute_snapshot_hash(symbols: list[str]) -> str:
    canonical = ",".join(sorted(symbols))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def map_to_constituents(
    records: list[dict], snapshot_date: date
) -> list[IndexConstituentCreate]:
    return [
        IndexConstituentCreate(
            index_name=SP500,
            snapshot_date=snapshot_date,
            symbol=r["symbol"].strip().upper(),
            company_name=r["company_name"].strip(),
            gics_sector=r["gics_sector"],
            gics_sub_industry=r["gics_sub_industry"],
            cik=str(r["cik"]).zfill(10),
        )
        for r in records
    ]
