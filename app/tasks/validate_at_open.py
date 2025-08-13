from datetime import date

import pandas as pd

from signals.filters import apply_validate_at_open_filters

from app.core.db import get_db
from app.handlers.eod_signal_handler import EODSignalHandler
from app.utils.trading_calendar import get_nth_previous_trading_day


def validate_signals_from_previous_trading_day():

    today = date.today()
    last_trading_day = get_nth_previous_trading_day(
        exchange="NYSE", as_of=today, lookback_days=1
    )

    with next(get_db()) as db_session:
        signals_to_validate = EODSignalHandler(db_session).get_unvalidated_for_date(
            last_trading_day
        )

        df = pd.DataFrame([signal.model_dump() for signal in signals_to_validate])
        strategy = df #'load_stragey_by_name()'
        validated_signals = strategy #'apply_validate_at_open_filters(strategy)'
        validated_signals = validated_signals
