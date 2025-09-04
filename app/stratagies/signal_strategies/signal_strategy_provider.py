from pathlib import Path
from typing import Final

from app.models.signal_strategy import SignalStrategy
from app.stratagies.strategy_provider import StrategyProvider

SIGNAL_STRATEGIES_DIR: Final = Path(__file__).parent  # .../signal_strategies


class SignalStrategyProvider(StrategyProvider[SignalStrategy]):
    STRATEGIES_DIR = Path(__file__).parent
    MODEL = SignalStrategy
    ID_FIELD = "strategy_id"
