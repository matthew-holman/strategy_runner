import pandas as pd

from app.models.strategy_config import FilterRule, RankingFormula, SignalStrategyConfig
from app.signals.filters import (
    apply_default_open_validation_filters,
    apply_default_signal_filters,
    apply_signal_filters,
    apply_validate_at_open_filters,
)

# ---------------------------
# Default EOD Filters (existing)
# ---------------------------


def test_apply_default_filters_removes_nan_and_bad_values():
    df = pd.DataFrame(
        [
            # Passes all checks
            {
                "close": 100,
                "volume": 2_000_000,
                "avg_volume": 1_500_000,
                "atr_14": 2,
                "strategy_score": 0.9,
            },
            # NaN field
            {
                "close": None,
                "volume": 2_000_000,
                "avg_volume": 1_500_000,
                "atr_14": 2,
                "strategy_score": 0.9,
            },
            # Low price
            {
                "close": 3,
                "volume": 2_000_000,
                "avg_volume": 1_500_000,
                "atr_14": 2,
                "strategy_score": 0.9,
            },
            # Low volume
            {
                "close": 100,
                "volume": 500_000,
                "avg_volume": 1_500_000,
                "atr_14": 2,
                "strategy_score": 0.9,
            },
            # Low ATR%
            {
                "close": 100,
                "volume": 2_000_000,
                "avg_volume": 1_500_000,
                "atr_14": 0.5,
                "strategy_score": 0.9,
            },
        ]
    )

    filtered = apply_default_signal_filters(df, {"close"})
    assert len(filtered) == 1
    assert filtered.iloc[0]["close"] == 100


# ---------------------------
# Strategy Filters (EOD)
# ---------------------------


def _minimal_ranking():
    # current schema expects a list of RankingFormula
    return [RankingFormula(indicator="close", function="linear", weight=1.0)]


def test_apply_strategy_filters_basic_value_comparison():
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "sma_50": 120, "close": 110},
            {"ticker": "MSFT", "sma_50": 90, "close": 100},
        ]
    )

    config = SignalStrategyConfig(
        strategy_id="test",
        name="SMA rule",
        signal_filters=[
            FilterRule(
                indicator="sma_50",
                comparison=">",
                value=1.0,
                comparison_field="close",
                note="SMA must be greater than close",
            )
        ],
        validate_at_open_filters=[],
        ranking=_minimal_ranking(),
        max_signals_per_day=5,
    )

    filtered = apply_signal_filters(df, config)
    assert len(filtered) == 1
    assert filtered.iloc[0]["ticker"] == "AAPL"


def test_apply_strategy_filters_between():
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "rsi_14": 45},
            {"ticker": "MSFT", "rsi_14": 65},
        ]
    )

    config = SignalStrategyConfig(
        strategy_id="test",
        name="RSI range filter",
        signal_filters=[
            FilterRule(
                indicator="rsi_14",
                comparison="between",
                min=40,
                max=60,
                value=1.0,  # present to satisfy schema, not used by 'between'
                note="RSI must be between 40 and 60",
            )
        ],
        validate_at_open_filters=[],
        ranking=_minimal_ranking(),
        max_signals_per_day=5,
    )

    filtered = apply_signal_filters(df, config)
    assert len(filtered) == 1
    assert filtered.iloc[0]["ticker"] == "AAPL"


def test_apply_strategy_filters_multiplier_of():
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "volume": 3_000_000, "avg_vol_20d": 1_000_000},
            {"ticker": "MSFT", "volume": 1_200_000, "avg_vol_20d": 1_000_000},
        ]
    )

    config = SignalStrategyConfig(
        strategy_id="test",
        name="Volume spike",
        signal_filters=[
            FilterRule(
                indicator="volume",
                comparison=">",
                value=2.0,
                comparison_field="avg_vol_20d",
                note="Volume > 2x avg",
            )
        ],
        validate_at_open_filters=[],
        ranking=_minimal_ranking(),
        max_signals_per_day=5,
    )

    filtered = apply_signal_filters(df, config)
    assert len(filtered) == 1
    assert filtered.iloc[0]["ticker"] == "AAPL"


# ---------------------------
# Default Open-Validation Filters (CURRENT impl: no staleness)
# ---------------------------


def test_apply_default_open_validation_filters_happy_path_and_liquidity():
    # row0 passes: floor met, liquidity 2% of 1M, gap ~+2%
    # row1 fails: liquidity 0.5% and price below floor
    df = pd.DataFrame(
        {
            "next_open": [10.0, 0.9],  # PRICE_FLOOR assumed 1.00 in impl
            "close": [9.8, 10.0],
            "atr_14": [0.2, 0.2],  # required core present
            "avg_vol_20d": [1_000_000, 1_000_000],
            "early_volume": [
                20_000,
                5_000,
            ],  # 2% vs 0.5% (MIN_EARLY_VOL_PERCENT = 0.01)
        }
    )
    required = {"next_open", "close", "atr_14", "avg_vol_20d", "early_volume"}

    out = apply_default_open_validation_filters(df.copy(), required)

    assert len(out) == 1
    assert out.iloc[0]["next_open"] == 10.0


def test_apply_default_open_validation_filters_gap_edge():
    close = 10.00
    valid_next_open = 10.49
    invalid_next_open = 10.51

    # row0 fails gap at 5.1%; row1 passes exactly at 5.0%
    df = pd.DataFrame(
        {
            "next_open": [invalid_next_open, valid_next_open],  # vs close=10.0
            "close": [close, close],
            "atr_14": [0.2, 0.2],
            "avg_vol_20d": [1_000_000, 1_000_000],
            "early_volume": [20_000, 20_000],  # 2% → meets liquidity
        }
    )
    required = {"next_open", "close", "atr_14", "avg_vol_20d", "early_volume"}

    out = apply_default_open_validation_filters(df.copy(), required)

    # Only the exactly-5%-gap row survives (assuming MAX_GAP_ABS = 0.05 is inclusive)
    assert len(out) == 1
    assert out.iloc[0]["next_open"] == valid_next_open


# ---------------------------
# Strategy Open-Validation Filters (NEW)
# ---------------------------


def test_apply_validate_at_open_filters_with_next_open_alias():
    # row0: +1.9% gap, ATR 2% of open → pass
    # row1: +2.5% gap → fail
    df = pd.DataFrame(
        {
            "next_open": [101.9, 102.5],
            "close": [100.0, 100.0],
            "atr_14": [2.0, 2.0],  # 2%
        }
    )

    cfg = SignalStrategyConfig(
        strategy_id="sma_pullback_buy",
        name="SMA PB",
        signal_filters=[],
        validate_at_open_filters=[
            FilterRule(
                indicator="open", comparison="<", value=1.02, comparison_field="close"
            ),
            FilterRule(
                indicator="open", comparison=">", value=0.98, comparison_field="close"
            ),
            FilterRule(
                indicator="atr_14", comparison=">", value=0.01, comparison_field="open"
            ),
        ],
        ranking=_minimal_ranking(),
        max_signals_per_day=5,
    )

    working = df.copy()
    working["open"] = working["next_open"]  # alias today's open for the filter engine
    out = apply_validate_at_open_filters(working, cfg)

    assert len(out) == 1
    assert out.iloc[0]["next_open"] == 101.9
