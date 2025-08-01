from datetime import date
from typing import List

from handlers.missing_ohlcv_data_event import MissingOHLCVDataEventHandler
from models.missing_ohlcv_data_event import MissingOHLCVDataEvent
from sqlmodel import Session


class MissingOHLCVDataEventService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.missing_handler = MissingOHLCVDataEventHandler(db_session)

    def emit(self, security_id: int, start_date: date, end_date: date):
        event = MissingOHLCVDataEvent(
            security_id=security_id,
            start_date=start_date,
            end_date=end_date,
        )
        self.missing_handler.save(event)
        self.db_session.commit()

    def get_pending(self) -> List[MissingOHLCVDataEvent]:
        return self.missing_handler.fetch_unprocessed()

    def mark_handled(self, event_id: int):
        return self.missing_handler.mark_as_handled(event_id)
