import json

from pathlib import Path

import pytest

from stratagies.signal_strategies import SignalStrategyProvider


def test_provider_loads_and_orders(tmp_path: Path):
    write_min_strategy_json(tmp_path, "sma_pullback_buy")
    provider = SignalStrategyProvider.from_directory(tmp_path)
    cfgs = list(provider.iter_strategies())
    assert len(cfgs) == 1
    assert cfgs[0].strategy_id == "sma_pullback_buy"


def test_id_mismatch_raises(tmp_path: Path):
    # filename 'foo.json' but strategy_id 'bar' → should raise
    write_min_strategy_json(tmp_path, "bar")  # creates bar.json
    (tmp_path / "foo.json").write_text((tmp_path / "bar.json").read_text())
    with pytest.raises(ValueError) as e:
        SignalStrategyProvider.from_directory(tmp_path)
    assert "ID mismatch" in str(e.value)


def write_min_strategy_json(dirpath: Path, strategy_id: str, **overrides) -> Path:
    data = {
        "strategy_id": strategy_id,
        "name": strategy_id.replace("_", " ").title(),
        "signal_filters": [],
        "validate_at_open_filters": [],
        "ranking": [{"indicator": "close", "function": "linear", "weight": 1.0}],
        "max_signals_per_day": 5,
    }
    data.update(overrides)
    p = dirpath / f"{strategy_id}.json"
    p.write_text(json.dumps(data))
    return p
