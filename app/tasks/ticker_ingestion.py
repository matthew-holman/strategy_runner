from __future__ import annotations

from app.core.db import get_db
from app.handlers.security import SecurityHandler
from app.models.security import Region, Security
from app.services.market_data_service import MarketDataService
from app.utils.log_wrapper import Log

DEFAULT_TICKER_LIMIT = 2000
BATCH_COMMIT_SIZE = 500


def region_security_sync(
    region: Region = Region.US, limit: int = DEFAULT_TICKER_LIMIT
) -> bool:
    """
    Refresh the security universe from Yahoo. Inserts any new tickers.
    Returns True if the universe changed (added or removed tickers).
    """
    Log.info(f"Fetching top {limit} U.S. equities from Yahoo...")
    target_tickers = set(
        MarketDataService().fetch_top_equities_by_region(region=region, limit=limit)
    )

    with next(get_db()) as db_session:
        security_symbols = SecurityHandler(db_session).get_all_symbols_for_region(
            region=region
        )
        existing_tickers: set[str] = set(security_symbols)

        new_symbols = sorted(target_tickers - existing_tickers)
        if not new_symbols:
            Log.info("No new securities to insert.")
            return False

        Log.info(f"Inserting {len(new_symbols)} new securities for region '{region}'.")

        securities = []
        for symbol in new_symbols:
            md = MarketDataService().fetch_ticker_metadata(symbol)

            # Provisional values to satisfy non-null columns (replace later in enrichment job)
            company_name = (md.company_name if md else None) or symbol
            gics_sector = (md.gics_sector if md else None) or "Provisional"
            gics_sub_industry = (md.gics_sub_industry if md else None) or "Provisional"

            security = Security(
                symbol=symbol,
                company_name=company_name,
                gics_sector=gics_sector,
                gics_sub_industry=gics_sub_industry,
                cik=(md.cik if md else None),
                first_trade_date=(md.first_trade_date if md else None),
                exchange=(md.exchange if md else None),
                region=region,
            )
            securities.append(security)

            if len(securities) % BATCH_COMMIT_SIZE == 0:
                SecurityHandler(db_session).save_all(securities)
                db_session.commit()
                Log.info(f"Inserted {len(securities)} securities.")
                securities = []

        SecurityHandler(db_session).save_all(securities)
        db_session.commit()
        Log.info(f"Inserted {len(securities)} securities.")
        return True
