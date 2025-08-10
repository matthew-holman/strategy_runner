import numpy as np
import pandas as pd

from app.models.strategy_config import StrategyConfig


def apply_strategy_ranking(
    df: pd.DataFrame, strategy_config: StrategyConfig
) -> pd.DataFrame:
    df = df.copy()
    df["score"] = 0.0

    for rule in strategy_config.ranking:
        indicator = rule.indicator
        weight = rule.weight
        func = rule.function

        if func == "gaussian":
            center = rule.center
            sigma = rule.sigma
            score_component = _gaussian_score(df[indicator], center, sigma)

        elif func == "log_ratio":
            denom = rule.denominator
            max_ratio = rule.max
            score_component = _log_ratio_score(df[indicator], df[denom], max_ratio)

        elif func == "linear":
            score_component = _linear_score(df[indicator])

        else:
            raise ValueError(f"Unsupported ranking function: {func}")

        df["score"] += weight * score_component

    # Sort and truncate to N results
    top_n = strategy_config.max_signals_per_day
    return df.sort_values(by="score", ascending=False).head(top_n)


def _gaussian_score(series, center, sigma):
    return np.exp(-((series - center) ** 2) / (2 * sigma**2))


def _log_ratio_score(numerator, denominator, max_ratio=None):
    ratio = np.log(numerator / denominator)
    if max_ratio:
        ratio = np.clip(ratio, None, np.log(max_ratio))
    return ratio


def _linear_score(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-9)
