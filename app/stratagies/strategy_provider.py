from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Generic, Iterator, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class StrategyProvider(Generic[T]):
    _by_id: dict[str, T]

    STRATEGIES_DIR: ClassVar[Path]  # set by subclass
    MODEL: ClassVar[type[BaseModel]]  # set by subclass
    ID_FIELD: ClassVar[str]  # set by subclass

    def __init__(self, by_id: dict[str, T]) -> None:
        self._by_id = by_id

    @classmethod
    def from_directory(
        cls: type[StrategyProvider[T]], root: Path | None = None
    ) -> StrategyProvider[T]:
        root = root or cls.STRATEGIES_DIR
        by_id: dict[str, T] = {}

        for path in sorted(root.glob("*.json")):
            raw = path.read_text(encoding="utf-8")
            cfg = cls.MODEL.model_validate_json(raw)
            file_id = path.stem

            if cfg.strategy_id != file_id:
                raise ValueError(
                    f"ID mismatch: file '{file_id}.json' vs cfg.strategy_id '{cfg.strategy_id}'"
                )

            if cfg.strategy_id in by_id:
                raise ValueError(
                    f"Duplicate strategy id '{cfg.strategy_id}' in {cls.STRATEGIES_DIR}"
                )

            by_id[cfg.strategy_id] = cfg

        return cls(by_id)

    def iter_strategies(self) -> Iterator[T]:
        for sid in sorted(self._by_id):
            yield self._by_id[sid]

    def get_by_id(self, strategy_id: str) -> T:
        try:
            return self._by_id[strategy_id]
        except KeyError as exc:
            raise KeyError(f"Unknown strategy id '{strategy_id}'") from exc
