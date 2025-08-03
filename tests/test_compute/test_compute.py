from datetime import date
from typing import List
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from freezegun import freeze_time
from indicators.compute import compute_indicators_for_range
from models.ohlcv_daily import OHLCVDaily
from sqlmodel import Session


@patch("app.handlers.ohlcv_daily.OHLCVDailyHandler")
@freeze_time("2024-12-31")
def test_compute_all_indicators_raises_on_insufficient_rows(mock_handler_cls):
    # Mock the handler and its method
    mock_handler = MagicMock()
    mock_handler_cls.return_value = mock_handler

    # Simulate only 150 rows of OHLCV data
    dates = pd.date_range(start="2024-06-01", periods=150, freq="B")
    mock_ohlcv_rows: List[OHLCVDaily] = [
        MagicMock(
            model_dump=lambda i=i, d=d: {
                "candle_date": date.today(),
                "open": float(i),
                "high": float(i + 1),
                "low": float(i - 1),
                "adjusted_close": float(i),
                "close": float(i),
                "volume": 1000 + i,
            }
        )
        for i, d in enumerate(dates)
    ]
    mock_handler.get_period_for_security.return_value = mock_ohlcv_rows

    session = MagicMock(spec=Session)
    compute_date = date(2024, 12, 31)

    with pytest.raises(RuntimeError) as exc_info:
        compute_indicators_for_range(
            security_id=1,
            start_date=compute_date,
            end_date=date.today(),
            session=session,
        )

    assert "Gaps in data" in str(exc_info.value)
