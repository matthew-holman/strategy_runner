import logging

from app.stratagies.execution_strategies import EXECUTION_STRATEGY_PROVIDER
from app.stratagies.signal_strategies import SIGNAL_STRATEGY_PROVIDER
from app.tasks.backtest_trades import generate_trades_for_signals
from app.utils import Log
from app.utils.log_setup import configure_logging


def main() -> int:

    configure_logging(logger_name="eod-tasks", level=logging.INFO, use_utc=False)

    try:
        for signal_strategy in SIGNAL_STRATEGY_PROVIDER.iter_strategies():
            Log.info(f"Generating historic signals for strategy {signal_strategy.name}")

            # generate_historic_signals_for_strategy(signal_strategy)
            for execution_strategy in EXECUTION_STRATEGY_PROVIDER.iter_strategies():
                generate_trades_for_signals(signal_strategy, execution_strategy)
            #
            # with next(get_db()) as db_session:
            #     BacktestRunHandler(db_session).save(backtest_run)
            #     db_session.commit()
    except Exception:
        # Captures full traceback
        Log.exception("Backtesting failed failed.")
        return 1

    Log.info("Backtest run completed successfully.")
    return 0


if __name__ == "__main__":
    main()
