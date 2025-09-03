# app/strategies/__init__.py
from pathlib import Path

from .signal_strategy_provider import SignalStrategyProvider

CURRENT_DIR = Path(__file__).parent
STRATEGY_PROVIDER = SignalStrategyProvider.from_directory(CURRENT_DIR)
