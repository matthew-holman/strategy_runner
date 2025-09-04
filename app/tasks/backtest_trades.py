from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

import pandas as pd

from dateutil.utils import today

from app.core.db import get_db
from app.handlers.backtest_trade import BacktestTradeHandler
from app.handlers.eod_signal import EODSignalHandler
from app.handlers.ohlcv_daily import OHLCVDailyHandler
from app.handlers.stock_index_constituent import StockIndexConstituentHandler
from app.handlers.technical_indicator import TechnicalIndicatorHandler
from app.models.backtest_run import BacktestRun
from app.models.backtest_trade import BacktestTrade, ExitReason
from app.models.signal_strategy import SignalStrategy
from app.models.stock_index_constituent import SP500
from app.utils.datetime_utils import chunk_date_range
from app.utils.log_wrapper import Log
from app.utils.trading_calendar import get_nth_trading_day


@dataclass(frozen=True)
class ExitEvent:
    exit_date: date
    exit_price: float
    exit_reason: ExitReason
    bars_held: int  # counts the entry bar as 1


def generate_trades_for_signals(
    backtest_run: BacktestRun, strategy_config: SignalStrategy
) -> None:
    config = backtest_run.backtest_config()

    with next(get_db()) as db_session:
        oldest_snapshot_date = (
            StockIndexConstituentHandler(db_session)
            .get_earliest_snapshot(SP500)
            .snapshot_date
        )

        backtest_handler = BacktestTradeHandler(db_session)

        for chunk_start, chunk_end in chunk_date_range(
            oldest_snapshot_date, today().date(), timedelta(days=365)
        ):

            signals = EODSignalHandler(db_session).get_by_strategy_between_dates(
                strategy_config.strategy_id, chunk_start, chunk_end
            )
            if not signals:
                Log.info(
                    f"No signals found for {strategy_config.strategy_id} in range {chunk_start}..{chunk_end}"
                )
                return
            trades: List[BacktestTrade] = []
            for eod_signal in signals:
                security_id: int = int(eod_signal.security_id)
                signal_date: date = eod_signal.signal_date

                technical_indicators = TechnicalIndicatorHandler(
                    db_session
                ).get_by_date_and_security_id(signal_date, security_id)
                if (
                    technical_indicators.atr_14 is None
                    or technical_indicators.atr_14 <= 0
                ):
                    Log.warning(
                        f"Skipping trade for {strategy_config.strategy_id} on {signal_date} "
                        f"(security_id={security_id}): ATR was {technical_indicators.atr_14}, "
                        "cannot compute stop/target or risk-adjusted metrics. "
                        "TODO: persist as skipped trade instead of dropping."
                    )
                    continue

                entry_day = get_nth_trading_day(
                    exchange="NYSE", as_of=signal_date, offset=1
                )  # TODO replace hardcoded exchange
                forward_end = get_nth_trading_day(
                    exchange="NYSE", as_of=entry_day, offset=config.max_holding_days - 1
                )

                ohlcv_data = OHLCVDailyHandler(db_session).get_period_for_security(
                    entry_day, forward_end, security_id
                )
                candles = pd.DataFrame([r.model_dump() for r in ohlcv_data])

                if candles.empty or entry_day not in set(candles["candle_date"]):
                    continue

                entry_bar = candles[candles["candle_date"] == entry_day].iloc[0]

                # for now assume entry price is open price
                # TODO add entry and exit strategy to strategy config
                entry_price = float(entry_bar["open"])
                stop_price = entry_price - config.k_stop * technical_indicators.atr_14
                target_price = (
                    entry_price + config.k_target * technical_indicators.atr_14
                )

                exit_event = decide_exit_for_long(
                    stop_price=stop_price,
                    target_price=target_price,
                    forward_bars=candles,
                    max_holding_days=config.max_holding_days,
                    conservative_intra_bar_rule=config.conservative_intra_bar_rule,
                    conservative_gap_rule=config.conservative_gap_rule,
                )

                pnl_percent = (exit_event.exit_price / entry_price - 1.0) * 100.0
                risk_per_share = entry_price - stop_price
                r_multiple = (
                    ((exit_event.exit_price - entry_price) / risk_per_share)
                    if risk_per_share > 0
                    else 0.0
                )

                trades.append(
                    BacktestTrade(
                        eod_signal_id=eod_signal.id,
                        strategy_id=strategy_config.strategy_id,
                        security_id=security_id,
                        entry_date=entry_day,
                        exit_date=exit_event.exit_date,
                        entry_price=entry_price,
                        exit_price=exit_event.exit_price,
                        stop_price=stop_price,
                        target_price=target_price,
                        atr_used=technical_indicators.atr_14,
                        pnl_percent=pnl_percent,
                        r_multiple=r_multiple,
                        bars_held=exit_event.bars_held,
                        exit_reason=exit_event.exit_reason,
                    )
                )

            backtest_handler.save_all(trades)
        db_session.commit()


def decide_exit_for_long(
    stop_price: float,
    target_price: float,
    forward_bars: pd.DataFrame,
    max_holding_days: int,
    conservative_intra_bar_rule: bool = True,
    conservative_gap_rule: bool = True,
) -> ExitEvent:
    bars = forward_bars.sort_values("candle_date").reset_index(drop=True)
    bars_held = 0

    for i, bar in bars.iterrows():
        d = bar["candle_date"]
        o, h, l, c = (
            float(bar["open"]),
            float(bar["high"]),
            float(bar["low"]),
            float(bar["close"]),
        )
        bars_held += 1

        if i == 0 and conservative_gap_rule:
            if o <= stop_price:
                return ExitEvent(d, o, ExitReason.stop, bars_held)
            if o >= target_price:
                return ExitEvent(d, o, ExitReason.target, bars_held)

        hit_stop = l <= stop_price
        hit_target = h >= target_price

        if hit_stop and hit_target:
            return ExitEvent(
                d,
                stop_price if conservative_intra_bar_rule else target_price,
                ExitReason.stop if conservative_intra_bar_rule else ExitReason.target,
                bars_held,
            )
        if hit_stop:
            return ExitEvent(d, stop_price, ExitReason.stop, bars_held)
        if hit_target:
            return ExitEvent(d, target_price, ExitReason.target, bars_held)

        if bars_held >= max_holding_days:
            return ExitEvent(d, c, ExitReason.time_stop, bars_held)

    last = bars.iloc[-1]
    return ExitEvent(
        last["candle_date"], float(last["close"]), ExitReason.time_stop, bars_held
    )
