from app.tasks.validate_at_open import validate_signals_from_previous_trading_day
from app.utils import Log
from app.utils.datetime_utils import today_is_a_weekend

logger = Log.setup(log_name="eod-tasks", application_name="daily-tasks")


def main():
    logger.info("Starting daily update tasks...")
    try:
        if today_is_a_weekend():
            logger.info("Today is a weekend, exchanges are closed.")
        else:
            validate_signals_from_previous_trading_day()
    except Exception as e:
        logger.critical(f"Daily tasks failed with exception: {e}")

    logger.info("All daily tasks completed successfully.")


if __name__ == "__main__":
    main()
