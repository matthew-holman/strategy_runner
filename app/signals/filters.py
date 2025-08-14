from typing import List

import pandas as pd

from app.models.strategy_config import FilterRule, StrategyConfig

# This assumes USD
# TODO replace with a currency specific version later
PRICE_FLOOR = 5

MIN_EARLY_VOL_PERCENT = 0.01
MAX_GAP_ABS = 0.05
OPEN_STALENESS_SECONDS = 60


def apply_default_signal_filters(
    df: pd.DataFrame, required_columns: set[str]
) -> pd.DataFrame:
    # 1. Drop rows with NaNs in required columns
    for col in required_columns:
        df = df[df[col].notna()]

    # 2. Apply price filter
    df = df[df["close"] >= PRICE_FLOOR]

    # 3. Apply volume filter
    df = df[df["volume"] >= 1_000_000]

    # 4. Apply ATR% filter: atr / entry_price >= 0.015
    df = df[(df["atr_14"] / df["close"]) >= 0.015]

    return df


def apply_default_open_validation_filters(
    df: pd.DataFrame, required_columns: set[str]
) -> pd.DataFrame:
    # 1) No Missing Core Fields
    for col in required_columns:
        df = df[df[col].notna()]

    # 2) Price floor on today's open
    df = df[df["next_open"] >= PRICE_FLOOR]

    # 3) Liquidity sanity check
    df = df[df["early_volume"] >= (MIN_EARLY_VOL_PERCENT * df["avg_vol_20d"])]

    # 4) Gap limit: |open/close - 1| <= MAX_GAP_ABS
    gap = (df["next_open"] / df["close"]) - 1.0
    df = df[gap.abs() <= MAX_GAP_ABS]

    # 5) Staleness / halt guard
    # sched = pd.to_datetime(df["scheduled_open_ts"], utc=True, errors="coerce")
    # seen = pd.to_datetime(df["open_seen_at"], utc=True, errors="coerce")
    # delta = (seen - sched).dt.total_seconds()
    # fresh_mask = (
    #     seen.notna() & sched.notna() & (delta >= 0) & (delta <= OPEN_STALENESS_SECONDS)
    # )
    # df = df[fresh_mask]

    return df


def apply_signal_filters(
    df: pd.DataFrame, strategy_config: StrategyConfig
) -> pd.DataFrame:
    return apply_filters(df, strategy_config.signal_filters)


def apply_validate_at_open_filters(
    df: pd.DataFrame, strategy_config: StrategyConfig
) -> pd.DataFrame:
    return apply_filters(df, strategy_config.validate_at_open_filters)


def apply_filters(df: pd.DataFrame, filters: List[FilterRule]) -> pd.DataFrame:
    """Return only rows that pass all rules."""
    if not filters:
        return df
    mask = pd.Series(True, index=df.index)
    for rule in filters:
        mask &= _build_filter_mask(df, rule)
    return df[mask].copy()


def _build_filter_mask(df: pd.DataFrame, rule: FilterRule) -> pd.Series:
    left_hand_side = rule.indicator

    if left_hand_side not in df.columns:
        raise ValueError(f"Missing indicator column in DataFrame: '{left_hand_side}'")

    # Determine the right-hand side of the comparison
    right_hand_side: pd.Series | float

    if rule.comparison == "between":
        # 'value' is not used for 'between' — it's min/max-based
        if rule.min is None or rule.max is None:
            raise ValueError(
                f"'between' comparison requires 'min' and 'max' values: {rule}"
            )
        return (df[left_hand_side] >= rule.min) & (df[left_hand_side] <= rule.max)

    # Otherwise, all other comparisons require a numeric 'value'
    base_value = rule.value

    if rule.comparison_field:
        right_hand_side_field = rule.comparison_field
        if right_hand_side_field not in df.columns:
            raise ValueError(
                f"Missing comparison field in DataFrame: '{right_hand_side_field}'"
            )
        right_hand_side = base_value * df[right_hand_side_field]
    else:
        right_hand_side = base_value

    # Apply the operator
    if rule.comparison == ">":
        return df[left_hand_side] > right_hand_side
    elif rule.comparison == "<":
        return df[left_hand_side] < right_hand_side
    elif rule.comparison == "==":
        return df[left_hand_side] == right_hand_side
    else:
        raise ValueError(f"Unsupported comparison operator: '{rule.comparison}'")
