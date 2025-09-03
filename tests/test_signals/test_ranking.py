import pandas as pd

from app.models.strategy_config import RankingFormula, SignalStrategyConfig
from app.signals.ranking import apply_strategy_ranking


def test_apply_strategy_ranking_gaussian():
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "rsi_14": 50},
            {"ticker": "MSFT", "rsi_14": 60},
            {"ticker": "GOOG", "rsi_14": 40},
        ]
    )

    config = SignalStrategyConfig(
        strategy_id="test",
        name="RSI Gaussian",
        signal_filters=[],
        ranking=[
            RankingFormula(
                indicator="rsi_14",
                function="gaussian",
                center=50,
                sigma=5,
                weight=1.0,
            )
        ],
        max_signals_per_day=3,
    )

    ranked = apply_strategy_ranking(df, config)
    assert ranked.iloc[0]["ticker"] == "AAPL"  # best score (centered)


def test_apply_strategy_ranking_log_ratio():
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "volume": 3_000_000, "avg_vol_20d": 1_000_000},
            {"ticker": "MSFT", "volume": 2_000_000, "avg_vol_20d": 1_000_000},
            {"ticker": "GOOG", "volume": 1_000_000, "avg_vol_20d": 1_000_000},
        ]
    )

    config = SignalStrategyConfig(
        strategy_id="test",
        name="Volume Spike",
        signal_filters=[],
        ranking=[
            RankingFormula(
                indicator="volume",
                function="log_ratio",
                denominator="avg_vol_20d",
                weight=1.0,
                max=5,
            )
        ],
        max_signals_per_day=2,
    )

    ranked = apply_strategy_ranking(df, config)
    assert list(ranked["ticker"]) == ["AAPL", "MSFT"]


def test_apply_strategy_ranking_linear():
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "close_position": 0.9},
            {"ticker": "MSFT", "close_position": 0.5},
            {"ticker": "GOOG", "close_position": 0.1},
        ]
    )

    config = SignalStrategyConfig(
        strategy_id="test",
        name="Close Pos Linear",
        signal_filters=[],
        ranking=[
            RankingFormula(
                indicator="close_position",
                function="linear",
                weight=1.0,
            )
        ],
        max_signals_per_day=3,
    )

    ranked = apply_strategy_ranking(df, config)
    assert ranked.iloc[0]["ticker"] == "AAPL"  # highest value


def test_apply_strategy_ranking_limits_top_n():
    df = pd.DataFrame(
        [
            {"ticker": "AAPL", "close_position": 0.9},
            {"ticker": "MSFT", "close_position": 0.5},
            {"ticker": "GOOG", "close_position": 0.1},
        ]
    )

    config = SignalStrategyConfig(
        strategy_id="test",
        name="Limit to 2",
        signal_filters=[],
        ranking=[
            RankingFormula(
                indicator="close_position",
                function="linear",
                weight=1.0,
            )
        ],
        max_signals_per_day=2,
    )

    ranked = apply_strategy_ranking(df, config)
    assert len(ranked) == 2
