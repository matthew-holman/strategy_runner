# app/strategies/__init__.py
from pathlib import Path

from app.stratagies.signal_strategies.signal_strategy_provider import (
    SignalStrategyProvider,
)

CURRENT_DIR = Path(__file__).parent
SIGNAL_STRATEGY_PROVIDER = SignalStrategyProvider.from_directory()
