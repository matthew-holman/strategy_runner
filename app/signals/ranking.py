import numpy as np
import pandas as pd

from app.models.signal_strategy import SignalStrategy


def apply_strategy_ranking(
    df: pd.DataFrame, strategy_config: SignalStrategy
) -> pd.DataFrame:
    df = df.copy()
    df["score"] = 0.0
    total_weight = 0.0

    for rule in strategy_config.ranking:
        indicator = rule.indicator
        weight = float(rule.weight)
        func = rule.function

        if indicator not in df.columns:
            raise KeyError(f"Missing indicator column '{indicator}' for ranking rule.")

        if func == "gaussian":
            assert rule.center is not None and rule.sigma is not None
            center = rule.center
            sigma = rule.sigma
            comp = _gaussian_score(df[indicator], center, sigma)  # ∈ [0,1]

        elif func == "log_ratio":
            assert rule.max is not None and rule.denominator is not None
            denom = rule.denominator
            max_ratio = rule.max
            if denom not in df.columns:
                raise KeyError(
                    f"Missing denominator column '{denom}' for log_ratio rule."
                )
            comp = _log_ratio_score(df[indicator], df[denom], max_ratio)  # ∈ [0,1]

        elif func == "linear":
            comp = _linear_score(df[indicator])  # ∈ [0,1]

        else:
            raise ValueError(f"Unsupported ranking function: {func}")

        df["score"] += weight * comp
        total_weight += weight

    if total_weight > 0:
        df["score"] /= total_weight  # weighted mean keeps score in [0,1]

    # Numerical guard against tiny FP drift
    df["score"] = df["score"].clip(0.0, 1.0)

    # Sort and truncate to N results
    top_n = strategy_config.max_signals_per_day
    return df.sort_values(by="score", ascending=False).head(top_n)


def _gaussian_score(series: pd.Series, center: float, sigma: float) -> pd.Series:
    # Pure Gaussian in [0,1]; NaNs → 0 contribution
    out = np.exp(-((series - center) ** 2) / (2 * (sigma**2)))
    return pd.Series(out, index=series.index).fillna(0.0)


def _log_ratio_score(
    numerator: pd.Series, denominator: pd.Series, max_ratio: float
) -> pd.Series:
    """
    Normalize log(numerator/denominator) to [0,1] with an upper cap of log(max_ratio).
    Below 1x → 0, at max_ratio → 1.
    """
    if max_ratio is None or max_ratio <= 1:
        raise ValueError("log_ratio requires 'max' > 1 to normalize to [0,1].")

    # Avoid division by zero/negatives; treat invalid as neutral (1x ⇒ 0 after log then clip)
    den = denominator.replace(0, np.nan)
    ratio = numerator / den
    ratio = ratio.replace([np.inf, -np.inf], np.nan).fillna(1.0)

    log_r = np.log(ratio)
    max_log = np.log(max_ratio)

    # Clip to [0, max_log] then normalize to [0,1]
    clipped = np.clip(log_r, 0.0, max_log)
    out = clipped / max_log
    return pd.Series(out, index=numerator.index).fillna(0.0)


def _linear_score(series: pd.Series) -> pd.Series:
    # Min-max to [0,1]; constant series → all zeros
    smin = series.min()
    smax = series.max()
    denom = smax - smin
    if denom == 0 or np.isclose(denom, 0.0):
        return pd.Series(0.0, index=series.index)
    out = (series - smin) / denom
    return pd.Series(out, index=series.index).fillna(0.0)
