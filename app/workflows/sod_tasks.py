import logging

from app.stratagies.signal_strategies import SIGNAL_STRATEGY_PROVIDER
from app.tasks.validate_at_open import validate_signals_from_previous_trading_day
from app.utils import Log
from app.utils.datetime_utils import today_is_a_weekend
from app.utils.log_setup import configure_logging

configure_logging(logger_name="sod-tasks", level=logging.INFO, use_utc=False)


def main():
    Log.info("Starting daily update tasks...")
    try:
        if today_is_a_weekend():
            Log.info("Today is a weekend, exchanges are closed.")
        else:
            for signal_strategy in SIGNAL_STRATEGY_PROVIDER.iter_strategies():
                Log.info(f"Validating eod signals for strategy {signal_strategy.name}.")
                validate_signals_from_previous_trading_day(signal_strategy)
    except Exception as e:
        Log.critical(f"Daily tasks failed with exception: {e}")

    Log.info("All daily tasks completed successfully.")


if __name__ == "__main__":
    main()
