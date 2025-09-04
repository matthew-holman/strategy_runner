from pathlib import Path

from app.models.execution_strategy import ExecutionStrategy
from app.stratagies.strategy_provider import StrategyProvider


class ExecutionStrategyProvider(StrategyProvider[ExecutionStrategy]):
    STRATEGIES_DIR = Path(__file__).parent
    MODEL = ExecutionStrategy
    ID_FIELD = "id"
