from dataclasses import dataclass
from typing import List

from sqlmodel import Session, select

from app.core.db import upsert
from app.models.missing_ohlcv_data_event import MissingOHLCVDataEvent


@dataclass
class MissingOHLCVDataEventHandler:
    db_session: Session

    def save(self, missing_event: MissingOHLCVDataEvent) -> None:
        upsert(
            model=MissingOHLCVDataEvent,
            db_session=self.db_session,
            constraint="uq_security_start_end",
            data_iter=[missing_event],
            exclude_columns={"id", "created_at", "updated_at"},
        )
        self.db_session.flush()

    def fetch_unprocessed(self) -> List[MissingOHLCVDataEvent]:
        statement = select(MissingOHLCVDataEvent).where(
            MissingOHLCVDataEvent.handled == False  # noqa: E712
        )
        return list(self.db_session.exec(statement))

    def mark_as_handled(self, event_id: int) -> None:
        event = self.db_session.get(MissingOHLCVDataEvent, event_id)
        if event:
            event.handled = True
            self.db_session.add(event)
            self.db_session.flush()
