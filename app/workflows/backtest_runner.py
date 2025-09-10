import logging

from app.core.db import get_db
from app.handlers.backtest_run import BacktestRunHandler
from app.models.backtest_run import BacktestRun
from app.stratagies.execution_strategies import EXECUTION_STRATEGY_PROVIDER
from app.stratagies.signal_strategies import SIGNAL_STRATEGY_PROVIDER
from app.tasks.backtest_trades import generate_trades_for_signals
from app.utils import Log
from app.utils.log_setup import configure_logging


def main() -> int:

    configure_logging(logger_name="backtest-runner", level=logging.INFO, use_utc=False)
    try:
        for signal_strategy in SIGNAL_STRATEGY_PROVIDER.iter_strategies():
            Log.info(f"Generating historic signals for strategy {signal_strategy.name}")

            backtest_run = BacktestRun(strategy_id=signal_strategy.strategy_id)
            # generate_historic_signals_for_strategy(signal_strategy)
            # validate_historic_signals_for_strategy_at_open(signal_strategy)
            for execution_strategy in EXECUTION_STRATEGY_PROVIDER.iter_strategies():
                if execution_strategy.active:
                    Log.info(
                        f"Generating historic trades for signal strategy {signal_strategy.name} "
                        f"and execution strategy {execution_strategy.strategy_id}"
                    )
                    generate_trades_for_signals(
                        signal_strategy, execution_strategy, backtest_run.run_id
                    )
                else:
                    # skipping inactive execution strategy
                    continue

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
