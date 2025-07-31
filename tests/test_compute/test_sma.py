import numpy as np
import pandas as pd

from app.indicators.sma import sma


def test_sma_returns_correct_final_value():
    # Close prices from 1 to 100
    df = pd.DataFrame({"adjusted_close": [float(i) for i in range(1, 101)]})

    # 5-day SMA: mean of 96, 97, 98, 99, 100
    expected_5 = sum(range(96, 101)) / 5
    result_5 = sma(df, lookback_days=5).iloc[-1]
    assert np.isclose(result_5, expected_5)

    # 10-day SMA: mean of 91 to 100
    expected_10 = sum(range(91, 101)) / 10
    result_10 = sma(df, lookback_days=10).iloc[-1]
    assert np.isclose(result_10, expected_10)

    # 50-day SMA: mean of 51 to 100
    expected_50 = sum(range(51, 101)) / 50
    result_50 = sma(df, lookback_days=50).iloc[-1]
    assert np.isclose(result_50, expected_50)
