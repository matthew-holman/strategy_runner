# app/strategies/repository.py
from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from app.models.strategy_config import SignalStrategyConfig


@dataclass
class SignalStrategyProvider:
    _by_id: dict[str, SignalStrategyConfig]

    def __init__(self, by_id: dict[str, SignalStrategyConfig]) -> None:
        self._by_id = by_id

    @classmethod
    def from_directory(cls, root: Path) -> SignalStrategyProvider:
        by_id: dict[str, SignalStrategyConfig] = {}
        for p in sorted(root.glob("*.json")):  # deterministic order
            raw = p.read_text()
            data = json.loads(raw)
            cfg = SignalStrategyConfig.model_validate(data)
            file_id = p.stem
            if cfg.strategy_id != file_id:
                raise ValueError(
                    f"ID mismatch: file '{file_id}.json' vs cfg.strategy_id '{cfg.strategy_id}'"
                )
            if cfg.strategy_id in by_id:
                raise ValueError(f"Duplicate strategy_id '{cfg.strategy_id}'")
            by_id[cfg.strategy_id] = cfg
        return cls(by_id)

    def iter_configs(self) -> Iterator[SignalStrategyConfig]:
        for sid in sorted(self._by_id):
            yield self._by_id[sid]

    def get_by_id(self, strategy_id: str) -> SignalStrategyConfig:
        try:
            return self._by_id[strategy_id]
        except KeyError as e:
            raise KeyError(f"Unknown strategy_id '{strategy_id}'") from e
