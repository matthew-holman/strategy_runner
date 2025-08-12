import pandas as pd

from app.models.strategy_config import FilterRule, StrategyConfig


def apply_default_filters(df: pd.DataFrame, required_columns: set[str]) -> pd.DataFrame:
    # 1. Drop rows with NaNs in required columns
    for col in required_columns:
        df = df[df[col].notna()]

    # 2. Apply price filter
    df = df[df["close"] >= 5]

    # 3. Apply volume filter
    df = df[df["volume"] >= 1_000_000]

    # 4. Apply ATR% filter: atr / entry_price >= 0.015
    df = df[(df["atr_14"] / df["close"]) >= 0.015]

    return df


def apply_strategy_filters(
    df: pd.DataFrame, strategy_config: StrategyConfig
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    for rule in strategy_config.signal_filters:
        rule_mask = _build_filter_mask(df, rule)
        mask &= rule_mask

    return df[mask]


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
