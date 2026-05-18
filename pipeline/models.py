from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AlphaCandidate:
    expression: str
    source: str
    strategy_type: str
    rationale: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    alpha_id: str | None = None


@dataclass(slots=True)
class SimulationMetrics:
    sharpe: float
    fitness: float
    annual_returns: float
    turnover: float
    drawdown: float
    self_correlation: float
    notes: str = ""
    checks: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class AgentReview:
    agent: str
    stage: str
    verdict: str
    summary: str
    confidence: float = 0.5


@dataclass(slots=True)
class PreBacktestMetrics:
    sharpe: float
    fitness: float
    annual_returns: float
    turnover: float
    drawdown: float
    self_correlation: float


@dataclass(slots=True)
class PreBacktestResult:
    passed: bool
    promoted: bool
    score: float
    confidence: float
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    theory_ids: list[str] = field(default_factory=list)
    analogs: list[dict[str, Any]] = field(default_factory=list)
    highest_similarity: float = 0.0
    estimated_metrics: PreBacktestMetrics = field(
        default_factory=lambda: PreBacktestMetrics(
            sharpe=0.0,
            fitness=0.0,
            annual_returns=0.0,
            turnover=0.0,
            drawdown=1.0,
            self_correlation=1.0,
        )
    )


@dataclass(slots=True)
class EvaluatedAlpha:
    candidate: AlphaCandidate
    metrics: SimulationMetrics
    validation_errors: list[str] = field(default_factory=list)
    gate_passed: bool = False
    gate_reasons: list[str] = field(default_factory=list)
    status: str = "tested"
    agent_reviews: list[AgentReview] = field(default_factory=list)


def normalized_verdict(value: str) -> str:
    upper = str(value or "").upper()
    if upper in {"PASS", "WARN", "FAIL"}:
        return upper
    return "WARN"


def aggregate_stage_verdict(reviews: list[AgentReview], stage: str) -> str | None:
    stage_reviews = [review for review in reviews if review.stage == stage]
    if not stage_reviews:
        return None
    verdicts = {normalized_verdict(review.verdict) for review in stage_reviews}
    if "FAIL" in verdicts:
        return "FAIL"
    if verdicts == {"PASS"}:
        return "PASS"
    return "WARN"


def average_stage_confidence(reviews: list[AgentReview], stage: str) -> float | None:
    scores = [float(review.confidence) for review in reviews if review.stage == stage]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 3)
