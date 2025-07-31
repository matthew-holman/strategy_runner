import pandas as pd

from app.indicators.ema import ema


def test_ema_returns_expected_final_value():
    # Increasing price series: [1.0, 2.0, ..., 100.0]
    df = pd.DataFrame({"adjusted_close": [float(i) for i in range(1, 101)]})

    result = ema(df, lookback_days=10)

    # Assert final value is near last close (since it's trending up)
    final_ema = result.iloc[-1]
    assert final_ema < 100.0  # Should lag behind
    assert final_ema > 90.0  # But not too far behind
    assert isinstance(final_ema, float)
