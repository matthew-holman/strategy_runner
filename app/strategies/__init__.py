# app/strategies/__init__.py
from pathlib import Path

from .strategy_provider import StrategyProvider

CURRENT_DIR = Path(__file__).parent
STRATEGY_PROVIDER = StrategyProvider.from_directory(CURRENT_DIR)
