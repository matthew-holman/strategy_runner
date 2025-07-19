import hashlib

from datetime import date

from core.db import get_db
from handlers.index_constituent import IndexConstituentHandler
from models.index_constituent import SP500, IndexConstituentCreate

from app.services.wiki_scraper import (
    fetch_wikipedia_html,
    parse_sp500_constituents_html,
)
from app.utils import Log

WIKI_PAGE = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def daily_sp500_sync():
    html = fetch_wikipedia_html(WIKI_PAGE)
    records = parse_sp500_constituents_html(html)
    Log.info(f"{len(records)} records parsed from S&P 500 Wikipedia page.")

    symbols = [r["symbol"] for r in records]
    snapshot_hash = compute_snapshot_hash(symbols)
    today = date.today()

    with next(get_db()) as db_session:
        ic_handler = IndexConstituentHandler(db_session)
        if ic_handler.snapshot_exists(SP500, snapshot_hash):
            Log.info("No changes detected in S&P 500 constituents — skipping insert.")
            return

        ic_objects = map_to_constituents(records, today, snapshot_hash)

        ic_handler.save_all(ic_objects)
        ic_handler.save_snapshot(SP500, snapshot_hash, today)
        db_session.commit()
        Log.info(
            f"{len(ic_objects)} records inserted for {today} with hash {snapshot_hash}"
        )


def compute_snapshot_hash(symbols: list[str]) -> str:
    canonical = ",".join(sorted(symbols))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def map_to_constituents(
    records: list[dict], snapshot_date: date, snapshot_hash: str
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
