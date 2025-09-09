from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

import pandas as pd

from dateutil.utils import today

from app.core.db import get_db
from app.handlers.backtest_trade import BacktestTradeHandler
from app.handlers.eod_signal import EODSignalHandler
from app.handlers.ohlcv_daily import OHLCVDailyHandler
from app.handlers.stock_index_constituent import StockIndexConstituentHandler
from app.handlers.technical_indicator import TechnicalIndicatorHandler
from app.models.backtest_trade import (
    BacktestTrade,
    EntryEvent,
    EntryReason,
    ExitEvent,
    ExitReason,
)
from app.models.execution_strategy import EntryMode, ExecutionStrategy, Unit
from app.models.signal_strategy import SignalStrategy
from app.models.stock_index_constituent import SP500
from app.models.technical_indicator import TechnicalIndicator
from app.utils.datetime_utils import chunk_date_range
from app.utils.log_wrapper import Log
from app.utils.trading_calendar import get_nth_trading_day


@dataclass(frozen=True)
class TradeBounds:
    stop_price: float
    target_price: float
    atr_used: Optional[float] = None


def generate_trades_for_signals(
    signal_strategy: SignalStrategy,
    execution_strategy: ExecutionStrategy,
    backtest_run_id: UUID,
) -> None:

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

            signals = EODSignalHandler(
                db_session
            ).get_validated_by_strategy_between_dates(
                signal_strategy.strategy_id, chunk_start, chunk_end
            )
            if not signals:
                Log.info(
                    f"No signals found for {signal_strategy.strategy_id} in range {chunk_start}..{chunk_end}"
                )
                return
            trades: List[BacktestTrade] = []
            for eod_signal in signals:
                security_id: int = int(eod_signal.security_id)
                signal_date: date = eod_signal.signal_date

                next_trading_day = get_nth_trading_day(
                    exchange="NYSE", as_of=signal_date, offset=1
                )  # TODO replace hardcoded exchange

                window_end = get_nth_trading_day(
                    exchange="NYSE",
                    as_of=next_trading_day,
                    offset=execution_strategy.max_hold_days,
                )  # TODO replace hardcoded exchange

                ohlcv_data = OHLCVDailyHandler(db_session).get_period_for_security(
                    next_trading_day, window_end, security_id
                )
                candles = pd.DataFrame([r.model_dump() for r in ohlcv_data])

                if candles.empty:
                    continue

                entry_event = compute_entry(candles, execution_strategy)
                if entry_event is None:
                    Log.info(
                        f"Entry setup did not meet criteria for security_id={security_id} "
                        f"on {signal_date} using execution strategy {execution_strategy.strategy_id}"
                    )
                    continue
                technical_indicators = TechnicalIndicatorHandler(
                    db_session
                ).get_by_date_and_security_id(entry_event.entry_date, security_id)
                if (
                    technical_indicators.atr_14 is None
                    or technical_indicators.atr_14 <= 0
                ):
                    Log.warning(
                        f"Skipping trade for {signal_strategy.strategy_id} on {entry_event.entry_date}"
                        f"(security_id={security_id}): ATR was {technical_indicators.atr_14}, "
                        "cannot compute stop/target or risk-adjusted metrics. "
                        "TODO: persist as skipped trade instead of dropping."
                    )
                    continue

                trade_bounds = compute_trade_bounds(
                    entry_event, execution_strategy, technical_indicators
                )

                exit_event = compute_exit(
                    trade_bounds,
                    forward_bars=candles,
                    execution_strategy=execution_strategy,
                )

                pnl_percent = (exit_event.exit_price / entry_event.price - 1.0) * 100.0
                risk_per_share = entry_event.price - trade_bounds.stop_price
                r_multiple = (
                    ((exit_event.exit_price - entry_event.price) / risk_per_share)
                    if risk_per_share > 0
                    else 0.0
                )

                trades.append(
                    BacktestTrade(
                        eod_signal_id=eod_signal.id,
                        signal_strategy_id=signal_strategy.strategy_id,
                        execution_strategy_id=execution_strategy.strategy_id,
                        security_id=security_id,
                        entry_date=entry_event.entry_date,
                        exit_date=exit_event.exit_date,
                        entry_price=entry_event.price,
                        exit_price=exit_event.exit_price,
                        stop_price=trade_bounds.stop_price,
                        target_price=trade_bounds.target_price,
                        atr_used=technical_indicators.atr_14,
                        pnl_percent=pnl_percent,
                        r_multiple=r_multiple,
                        bars_held=exit_event.bars_held,
                        exit_reason=exit_event.exit_reason,
                        run_id=backtest_run_id,
                    )
                )

            backtest_handler.save_all(trades)
        db_session.commit()


def compute_exit(
    trade_bounds: TradeBounds,
    forward_bars: pd.DataFrame,
    execution_strategy: ExecutionStrategy,
) -> ExitEvent:

    bars = forward_bars.sort_values("candle_date").reset_index(drop=True)
    bars_held = 0

    for _i, bar in bars.iterrows():
        candle_date = bar["candle_date"]
        high, low, close = (
            float(bar["high"]),
            float(bar["low"]),
            float(bar["close"]),
        )
        bars_held += 1

        hit_stop = low <= trade_bounds.stop_price
        hit_target = high >= trade_bounds.target_price

        # in this scenario assume we hit stop first
        # no way to know for sure but testing is best if conservative
        if hit_stop and hit_target:
            return ExitEvent(
                candle_date,
                trade_bounds.stop_price,
                ExitReason.stop,
                bars_held,
            )
        if hit_stop:
            return ExitEvent(
                candle_date, trade_bounds.stop_price, ExitReason.stop, bars_held
            )
        if hit_target:
            return ExitEvent(
                candle_date, trade_bounds.target_price, ExitReason.target, bars_held
            )

        if bars_held >= execution_strategy.max_hold_days:
            return ExitEvent(candle_date, close, ExitReason.time_stop, bars_held)

    last = bars.iloc[-1]
    return ExitEvent(
        last["candle_date"], float(last["close"]), ExitReason.time_stop, bars_held
    )


def compute_entry(
    candles: pd.DataFrame,
    execution_strategy: ExecutionStrategy,
) -> Optional[EntryEvent]:
    if candles.empty:
        return None

    entry_mode = execution_strategy.entry.mode

    if entry_mode == EntryMode.IMMEDIATE_AT_OPEN:
        bar = candles.iloc[0]
        return EntryEvent(
            entry_date=pd.to_datetime(bar["candle_date"]).date(),
            price=float(bar["open"]),
            entry_reason=EntryReason.IMMEDIATE_AT_OPEN,
            bars_waited=0,
        )

    if entry_mode == EntryMode.PERCENT_UNDER_OPEN:
        pct = execution_strategy.entry.percent_below_open
        window = execution_strategy.entry.valid_for_bars
        if pct is None or pct <= 0 or window is None or window < 1:
            return None

        window_end = min(window, len(candles))
        for i in range(window_end):
            bar = candles.iloc[i]
            open_price = float(bar["open"])
            low_price = float(bar["low"])
            buy_price = open_price * (1.0 - pct)

            if low_price <= buy_price:
                # Floating definition: fill at limit; open is always > limit here.
                return EntryEvent(
                    entry_date=pd.to_datetime(bar["candle_date"]).date(),
                    price=float(buy_price),
                    entry_reason=EntryReason.WAIT_TRIGGER,
                    bars_waited=i,
                )
        return None

    # TODO: add WAIT logic later
    return None


def compute_trade_bounds(
    entry_event: EntryEvent,
    execution_strategy: ExecutionStrategy,
    technical_indicators: TechnicalIndicator,
) -> TradeBounds:
    """
    v0 behavior: ATR-based stop/target around entry_price.
    Designed to extend later with percent/points units without touching call sites.
    """
    stop_off = execution_strategy.exit.stop_offset
    target_off = execution_strategy.exit.target_offset

    atr_value: Optional[float] = None

    def resolve_offset(unit: Unit, multiple: float) -> float:
        nonlocal atr_value
        if unit == Unit.ATR:
            # pull the same ATR you already compute (14 by default in BacktestConfig)
            atr = getattr(technical_indicators, "atr_14", None)
            if atr is None or atr <= 0:
                raise ValueError(
                    "ATR is required and must be positive for ATR-based offsets."
                )
            atr_value = float(atr)
            return multiple * atr_value
        elif unit.name == "PERCENT":  # in case you add later
            return entry_event.price * multiple
        elif unit.name == "POINTS":  # in case you add later
            return multiple
        else:
            raise NotImplementedError(f"Unsupported offset unit: {unit}")

    stop_delta = resolve_offset(stop_off.unit, float(stop_off.multiple))
    target_delta = resolve_offset(target_off.unit, float(target_off.multiple))

    return TradeBounds(
        stop_price=float(entry_event.price - stop_delta),
        target_price=float(entry_event.price + target_delta),
        atr_used=atr_value,
    )
