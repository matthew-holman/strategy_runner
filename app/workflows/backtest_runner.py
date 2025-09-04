import logging

from app.core.db import get_db
from app.handlers.backtest_run import BacktestRunHandler
from app.models.backtest_run import BacktestRun
from app.stratagies.signal_strategies import SIGNAL_STRATEGY_PROVIDER
from app.tasks.backtest_trades import generate_trades_for_signals
from app.utils import Log
from app.utils.log_setup import configure_logging


def main() -> int:

    configure_logging(logger_name="eod-tasks", level=logging.INFO, use_utc=False)

    try:
        for strategy_config in SIGNAL_STRATEGY_PROVIDER.iter_configs():
            Log.info(f"Generating historic signals for strategy {strategy_config.name}")

            backtest_run = BacktestRun(strategy_id=strategy_config.strategy_id)
            # generate_historic_signals_for_config(strategy_config)
            generate_trades_for_signals(backtest_run, strategy_config)

            with next(get_db()) as db_session:
                BacktestRunHandler(db_session).save(backtest_run)
                db_session.commit()
    except Exception:
        # Captures full traceback
        Log.exception("Backtesting failed failed.")
        return 1

    Log.info("Backtest run completed successfully.")
    return 0


if __name__ == "__main__":
    main()
