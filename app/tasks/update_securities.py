import urllib.error

from app.core.db import get_db
from app.handlers.security import SecurityHandler
from app.services.market_data_service import MarketDataService
from app.utils.log_wrapper import Log


def check_for_missing_metadata():

    with next(get_db()) as db_session:
        security_handler = SecurityHandler(db_session)

        securities_to_update = security_handler.get_with_missing_metadata()
        Log.info(f"Updating metadata for {len(securities_to_update)}")

        for security in securities_to_update:
            try:
                metadata = MarketDataService.fetch_ticker_metadata(
                    security_symbol=security.symbol
                )
                security.exchange = metadata["exchange"]
                security.first_trade_date = metadata["first_trade_date"]
                db_session.flush()
            except (KeyError, urllib.error.HTTPError, ValueError) as e:
                Log.error(f"Failed to update {security.symbol}, caught error: {e}")
                continue
            except Exception as e:
                Log.error(f"Failed to update {security.symbol}, caught error: {e}")
                continue

        db_session.commit()
