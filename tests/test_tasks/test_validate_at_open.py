import pandas as pd
import pytest

from app.models.strategy_config import FilterRule, RankingFormula, SignalStrategyConfig
from app.tasks.validate_at_open import (
    apply_at_open_filters,  # adjust import if file differs
)


@pytest.fixture
def mock_config_sma_pullback() -> SignalStrategyConfig:

    return SignalStrategyConfig(
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
        ranking=[RankingFormula(indicator="close", function="linear", weight=1.0)],
        max_signals_per_day=5,
    )


def test_apply_at_open_filters_basic(monkeypatch, mock_config_sma_pullback):
    """
    id=1 → +1.9% gap, ATR 2% of open → pass
    id=2 → +2.5% gap → fail
    """
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "strategy_id": ["sma_pullback_buy", "sma_pullback_buy"],
            "next_open": [101.9, 102.5],
            "close": [100.0, 100.0],
            "atr_14": [2.0, 2.0],  # 2% of open ~= pass threshold
            "avg_vol_20d": [1_000_000, 1_000_000],
            "early_volume": [20_000, 20_000],  # 2% liquidity (>=1% passes)
        }
    )

    # Mock STRATEGY_PROVIDER.get_by_id in the correct module namespace
    import app.tasks.validate_at_open as mod

    monkeypatch.setattr(
        mod.STRATEGY_PROVIDER, "get_by_id", lambda sid: mock_config_sma_pullback
    )

    out = apply_at_open_filters(df)

    assert out.loc[out["id"] == 1, "validated_at_open"].item() is True
    assert out.loc[out["id"] == 2, "validated_at_open"].item() is False


def test_apply_at_open_filters_missing_open_sets_none(
    monkeypatch, mock_config_sma_pullback
):
    """
    id=10 has next_open=None → validated_at_open should remain None.
    id=11 has valid open and passes all defaults/strategy rules → True.
    """
    df = pd.DataFrame(
        {
            "id": [10, 11],
            "strategy_id": ["sma_pullback_buy", "sma_pullback_buy"],
            "next_open": [None, 101.0],
            "close": [100.0, 100.0],
            "atr_14": [2.0, 2.0],
            "avg_vol_20d": [1_000_000, 1_000_000],
            "early_volume": [20_000, 20_000],
        }
    )

    import app.tasks.validate_at_open as mod

    monkeypatch.setattr(
        mod.STRATEGY_PROVIDER, "get_by_id", lambda sid: mock_config_sma_pullback
    )

    out = apply_at_open_filters(df)

    # None for missing open
    assert pd.isna(out.loc[out["id"] == 10, "validated_at_open"]).item()

    # True for the passing row
    assert out.loc[out["id"] == 11, "validated_at_open"].item() is True
