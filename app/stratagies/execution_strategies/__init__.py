# app/strategies/__init__.py
from pathlib import Path

from app.stratagies.execution_strategies.execution_strategy_provider import (
    ExecutionStrategyProvider,
)

CURRENT_DIR = Path(__file__).parent
EXECUTION_STRATEGY_PROVIDER = ExecutionStrategyProvider.from_directory()
