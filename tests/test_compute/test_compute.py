from datetime import date, timedelta
from typing import List
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from freezegun import freeze_time

from app.indicators.compute import compute_indicators_for_range
from app.indicators.exceptions import InsufficientOHLCVDataError
from app.models.ohlcv_daily import OHLCVDaily


@patch("app.handlers.ohlcv_daily.OHLCVDailyHandler")
@freeze_time("2024-12-31")
def test_compute_all_indicators_raises_on_insufficient_rows(
    mock_handler_cls, db_session
):
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

    compute_date = date(2024, 12, 31)

    security_id = 1

    with pytest.raises(InsufficientOHLCVDataError) as exc_info:
        compute_indicators_for_range(
            security_id=security_id,
            start_date=compute_date,
            end_date=date.today(),
            session=db_session,
        )

    assert f"Insufficient OHLCV data for security {security_id} " in str(exc_info.value)


@pytest.fixture
def dummy_ohlcv_df_divide_by_zero():
    base_date = date(2020, 1, 1)
    return pd.DataFrame(
        {
            "candle_date": [base_date + timedelta(days=i) for i in range(200)],
            "open": [100.0] * 200,
            "high": [100.0] * 200,
            "low": [100.0] * 200,
            "close": [100.0] * 200,  # constant price —> RSI division by 0
            "adjusted_close": [100.0] * 200,
            "volume": [0.0] * 200,  # zero volume —> average volume issue
        }
    )


@patch("app.indicators.compute._load_ohlcv_df")
def test_compute_indicators_divide_by_zero(
    mock_load, dummy_ohlcv_df_divide_by_zero, db_session
):
    # Given
    mock_load.return_value = dummy_ohlcv_df_divide_by_zero
    start = date(2020, 7, 4)
    end = date(2020, 7, 18)

    # When
    df = compute_indicators_for_range(
        security_id=1, start_date=start, end_date=end, session=db_session
    )

    # Then
    assert not df.empty
    assert len(df) == 15

    # avg_vol_20d should be NaN for all rows due to volume=0
    assert "avg_vol_20d" in df.columns
    assert (
        df["avg_vol_20d"].isnull().all()
    ), "avg_vol_20d should be NaN when all volume is 0"
