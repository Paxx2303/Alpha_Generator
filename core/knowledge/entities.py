"""Typed domain entities for the knowledge layer."""
from __future__ import annotations
from pydantic import BaseModel, Field


class OperatorFact(BaseModel):
    name: str
    category: str                    # ts_*, group_*, cross_*
    scope: str = ""                  # e.g. "MATRIX", "VECTOR"
    definition: str = ""
    validated: bool = True
    use_cases: list[str] = Field(default_factory=list)
    broken_note: str | None = None   # e.g. "unavailable on WQB"


class FieldFact(BaseModel):
    name: str
    dataset: str = ""
    category: str = ""              # fundamental|technical|estimate|macro
    proven_ic_range: tuple[float, float] | None = None
    notes: str = ""


class AlphaPattern(BaseModel):
    family: str                     # "Fundamental_Corr", "Intraday_Reversal"
    formula_template: str
    avg_sharpe: float = 0.0
    avg_fitness: float = 0.0
    best_settings: dict = Field(default_factory=dict)
    source_ids: list[str] = Field(default_factory=list)
    alpha_count: int = 0
