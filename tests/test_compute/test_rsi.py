import pandas as pd

from app.indicators.rsi import rsi


def test_rsi_returns_expected_final_value():
    # Price goes up for 14 days, then down for 14 days
    gains = [100 + i for i in range(14)]
    losses = [
        113 - i for i in range(14)
    ]  # Starts lower than last gain price to avoid zero delta
    prices = gains + losses

    df = pd.DataFrame({"adjusted_close": prices})

    result = rsi(df, lookback_days=14)

    final_rsi = result.iloc[-1]

    # Should be low after losing streak (RSI drops)
    assert 0 <= final_rsi <= 100
    assert final_rsi < 50
    assert isinstance(final_rsi, float)
