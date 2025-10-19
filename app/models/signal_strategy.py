from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class FilterRule(BaseModel):
    indicator: str  # Field being evaluated
    comparison: Literal["<", ">", "==", "between"]
    value: float  # Constant threshold or multiplier base
    min: Optional[float] = None  # For "between"
    max: Optional[float] = None  # For "between"
    comparison_field: Optional[str] = None  # For field-to-field comparison
    note: Optional[str] = None  # Human-readable description

    @model_validator(mode="before")
    def check_comparison_fields(cls, values):
        comparison = values.get("comparison")
        value = values.get("value")
        min_val = values.get("min")
        max_val = values.get("max")
        comparison_field = values.get("comparison_field")

        if comparison == "between":
            if min_val is None or max_val is None:
                raise ValueError("`between` comparison requires both `min` and `max`.")
            if comparison_field:
                raise ValueError("`comparison_field` is not supported with 'between'.")
        else:
            if value is None:
                raise ValueError(f"`{comparison}` comparison requires `value`.")
        return values


class RankingFormula(BaseModel):
    indicator: str
    function: Literal["gaussian", "log_ratio", "linear"]
    weight: float
    # Function-specific parameters
    center: Optional[float] = None  # For gaussian
    sigma: Optional[float] = None  # For gaussian
    denominator: Optional[str] = None  # For log_ratio
    max: Optional[float] = None  # Optional cap on score

    @model_validator(mode="before")
    @classmethod
    def validate_function_params(cls, values):
        func = values.get("function")

        if func == "gaussian":
            if values.get("center") is None or values.get("sigma") is None:
                raise ValueError("Gaussian scoring requires 'center' and 'sigma'.")

        if func == "log_ratio":
            if values.get("denominator") is None:
                raise ValueError("Log ratio scoring requires 'denominator'.")

        return values


class SignalStrategy(BaseModel):
    active: bool = False
    strategy_id: str
    name: str
    signal_filters: List[FilterRule]

    # NEW: validation-at-open rules (same schema as filters)
    validate_at_open_filters: list[FilterRule] = Field(default_factory=list)

    ranking: List[RankingFormula]
    max_signals_per_day: int = Field(default=5)

    def required_eod_columns(self) -> set[str]:
        cols = {
            "close",
            "volume",
            "avg_vol_20d",
            "atr_14",
        }  # needed for default filters
        for rule in self.signal_filters:
            cols.add(rule.indicator)
            if rule.comparison_field:
                cols.add(rule.comparison_field)
        # Ranking requirements
        for r in self.ranking:
            cols.add(r.indicator)
            if r.denominator:
                cols.add(r.denominator)
        return cols

    def required_sod_columns(self) -> set[str]:
        cols = {
            "close",
            "volume",
            "avg_vol_20d",
            "atr_14",
        }  # needed for default filters
        for rule in self.validate_at_open_filters:
            cols.add(rule.indicator)
            if rule.comparison_field:
                cols.add(rule.comparison_field)
        # Ranking requirements
        for r in self.ranking:
            cols.add(r.indicator)
            if r.denominator:
                cols.add(r.denominator)
        return cols
