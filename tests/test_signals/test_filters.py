import pandas as pd

from app.models.strategy_config import FilterRule, StrategyConfig
from app.signals.filters import apply_default_filters, apply_signal_filters

# ---------------------------
# Default Filters
# ---------------------------


def test_apply_default_filters_removes_nan_and_bad_values():
    df = pd.DataFrame(
        [
            # Passes all checks
            {
                "entry_price": 100,
                "volume": 2_000_000,
                "avg_volume": 1_500_000,
                "atr": 2,
                "strategy_score": 0.9,
            },
            # NaN field
            {
                "entry_price": None,
                "volume": 2_000_000,
                "avg_volume": 1_500_000,
                "atr": 2,
                "strategy_score": 0.9,
            },
            # Low price
            {
                "entry_price": 3,
                "volume": 2_000_000,
                "avg_volume": 1_500_000,
                "atr": 2,
                "strategy_score": 0.9,
            },
            # Low volume
            {
                "entry_price": 100,
                "volume": 500_000,
                "avg_volume": 1_500_000,
                "atr": 2,
                "strategy_score": 0.9,
            },
            # Low ATR%
            {
                "entry_price": 100,
                "volume": 2_000_000,
                "avg_volume": 1_500_000,
                "atr": 0.5,
                "strategy_score": 0.9,
            },
        ]
    )

    filtered = apply_default_filters(df)
    assert len(filtered) == 1
    assert filtered.iloc[0]["entry_price"] == 100


# ---------------------------
# Strategy Filters
# ---------------------------


def test_apply_strategy_filters_basic_value_comparison():
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "sma_50": 120, "close": 110},
            {"ticker": "MSFT", "sma_50": 90, "close": 100},
        ]
    )

    config = StrategyConfig(
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
        ranking={"formula": []},
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

    config = StrategyConfig(
        strategy_id="test",
        name="RSI range filter",
        signal_filters=[
            FilterRule(
                indicator="rsi_14",
                comparison="between",
                min=40,
                max=60,
                value=1.0,  # not used but required
                note="RSI must be between 40 and 60",
            )
        ],
        ranking={"formula": []},
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

    config = StrategyConfig(
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
        ranking={"formula": []},
        max_signals_per_day=5,
    )

    filtered = apply_signal_filters(df, config)
    assert len(filtered) == 1
    assert filtered.iloc[0]["ticker"] == "AAPL"
