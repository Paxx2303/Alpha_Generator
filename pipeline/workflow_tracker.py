from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import re
import uuid
from typing import Any

from database import AlphaStore
from pipeline.models import AgentReview, AlphaCandidate, SimulationMetrics


FIELD_INFO = {
    "returns": {"description": "Daily close-to-close return.", "type": "MATRIX", "source": "Brain built-in"},
    "close": {"description": "Daily close price.", "type": "MATRIX", "source": "Brain built-in"},
    "volume": {"description": "Daily traded volume.", "type": "MATRIX", "source": "Brain built-in"},
    "vwap": {"description": "Volume-weighted average price.", "type": "MATRIX", "source": "Brain built-in"},
}
OPERATOR_INFO = {
    "rank": {"definition": "Cross-sectional rank of x.", "reason": "Improves robustness and controls outliers."},
    "ts_mean": {"definition": "Rolling mean over d periods.", "reason": "Smooths noise and often lowers turnover."},
    "ts_delta": {"definition": "Difference from value d periods ago.", "reason": "Measures directional displacement."},
    "ts_std_dev": {"definition": "Rolling standard deviation.", "reason": "Normalizes by recent volatility."},
    "ts_corr": {"definition": "Rolling correlation of two series.", "reason": "Captures interaction and confirmation patterns."},
    "zscore": {"definition": "Standard score.", "reason": "Puts values on a comparable scale."},
}
THEORY_RULES = {
    "beh-overreaction": "reversion",
    "beh-underreaction": "momentum",
    "econ-microstructure": "volume",
    "econ-liquidity-premium": "volume",
    "stat-order-statistics": "rank(",
    "stat-garch": "ts_std_dev",
    "beh-anchoring": "close / ts_mean(close",
    "info-entropy": "vwap",
}


def parse_expression_features(expression: str) -> dict[str, Any]:
    expr = expression.lower()
    fields = sorted({token for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr) if token in FIELD_INFO})
    operators = sorted({token for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr) if token in OPERATOR_INFO})
    if "ts_corr(volume" in expr:
        theme = "Liquidity-confirmed momentum"
        hypothesis = "Volume and return are moving together, so participation may still be reinforcing price direction."
    elif "volume / ts_mean(volume" in expr:
        theme = "Liquidity regime shift"
        hypothesis = "Sustained abnormal volume can reflect a structural participation shift rather than a one-day spike."
    elif "-ts_delta(vwap" in expr or "-ts_delta(close" in expr:
        theme = "Short-term reversal"
        hypothesis = "Recent losers may bounce when panic flow fades or the market overreacts."
    elif "close / ts_mean(close" in expr:
        theme = "Price versus local anchor"
        hypothesis = "Distance from a rolling mean can encode anchoring, drift, or mean-reversion pressure."
    elif "ts_delta(close" in expr and "ts_std_dev" in expr:
        theme = "Volatility-normalized trend"
        hypothesis = "Directional movement matters when it survives scaling by recent volatility."
    else:
        theme = "Return persistence"
        hypothesis = "Recent cross-sectional return leadership may persist if information diffuses gradually."
    return {"theme": theme, "hypothesis": hypothesis, "fields": fields, "operators": operators}


def match_theory_ids(expression: str) -> list[str]:
    expr = expression.lower()
    matched: list[str] = []
    for theory_id, needle in THEORY_RULES.items():
        if needle in expr:
            matched.append(theory_id)
    if ("ts_mean(returns" in expr or "ts_delta(close" in expr) and "beh-underreaction" not in matched:
        matched.append("beh-underreaction")
    if ("-ts_delta" in expr or "-(close / ts_mean" in expr) and "beh-overreaction" not in matched:
        matched.append("beh-overreaction")
    return matched[:5]


def default_risks(theme: str) -> list[str]:
    risks = [
        "High self-correlation can still block submission even when headline metrics look strong.",
        "Turnover above the fitness floor can erode otherwise attractive Sharpe.",
    ]
    if "reversal" in theme.lower():
        risks.append("Reversal can break during strong trending regimes.")
    if "momentum" in theme.lower():
        risks.append("Momentum motifs can become crowded and decay faster when flows reverse.")
    if "liquidity" in theme.lower():
        risks.append("Liquidity signals can change character in stressed markets and around event clusters.")
    return risks


def build_expected_metrics(thresholds: dict[str, float]) -> dict[str, Any]:
    return {
        "sharpe": f">= {thresholds['sharpe_min']}",
        "fitness": f">= {thresholds['fitness_min']}",
        "turnover": f"{thresholds['turnover_min']} - {thresholds['turnover_max']}",
        "drawdown": f"<= {thresholds['drawdown_max']}",
        "self_correlation": f"<= {thresholds['self_correlation_max']}",
    }


class WorkflowTracker:
    def __init__(
        self,
        store: AlphaStore,
        workflow_type: str,
        strategy_type: str,
        target_count: int,
        submit_enabled: bool,
        dry_run: bool,
        run_tags: dict[str, Any] | None = None,
    ) -> None:
        self.store = store
        self.workflow_type = workflow_type
        self.strategy_type = strategy_type
        self.target_count = target_count
        self.submit_enabled = submit_enabled
        self.dry_run = dry_run
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        self.run_id = f"{workflow_type}-{strategy_type}-{stamp}-{uuid.uuid4().hex[:8]}"
        self.current_stage = "research"
        self.store.create_pipeline_run(
            run_id=self.run_id,
            workflow_type=workflow_type,
            strategy_type=strategy_type,
            target_count=target_count,
            submit_enabled=submit_enabled,
            dry_run=dry_run,
            tags=run_tags or {},
        )

    def set_stage(self, stage: str, detail: str, *, status: str = "running", payload: dict[str, Any] | None = None) -> None:
        self.current_stage = stage
        self.store.update_pipeline_run(self.run_id, status=status, current_stage=stage)
        self.event(stage, "INFO", "stage", detail, payload=payload)

    def event(
        self,
        stage: str,
        level: str,
        event_type: str,
        message: str,
        *,
        alpha_expression: str | None = None,
        alpha_run_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.store.add_pipeline_event(
            run_id=self.run_id,
            stage=stage,
            level=level,
            event_type=event_type,
            message=message,
            alpha_expression=alpha_expression,
            alpha_run_id=alpha_run_id,
            payload=payload,
        )

    def research_artifact(
        self,
        kind: str,
        title: str,
        content: str,
        *,
        query_text: str | None = None,
        source_path: str | None = None,
        related_alpha_expression: str | None = None,
        score: float | None = None,
    ) -> int:
        return self.store.save_research_artifact(
            run_id=self.run_id,
            kind=kind,
            title=title,
            content=content,
            query_text=query_text,
            source_path=source_path,
            related_alpha_expression=related_alpha_expression,
            score=score,
        )

    def alpha_explanation(
        self,
        alpha_run_id: int,
        candidate: AlphaCandidate,
        *,
        thresholds: dict[str, float],
        prompt_context: str,
        research_refs: list[dict[str, Any]] | None = None,
        agent_reviews: list[AgentReview] | None = None,
        stage_notes: dict[str, Any] | None = None,
    ) -> None:
        features = parse_expression_features(candidate.expression)
        payload = {
            "theme": features["theme"],
            "hypothesis": features["hypothesis"],
            "prompt_context": prompt_context[:5000],
            "expected_metrics": build_expected_metrics(thresholds),
            "risks": default_risks(features["theme"]),
            "theory_ids": match_theory_ids(candidate.expression),
            "research_refs": research_refs or [],
            "field_info": [{"field": name, **FIELD_INFO[name]} for name in features["fields"]],
            "operator_info": [{"operator": name, **OPERATOR_INFO[name]} for name in features["operators"]],
            "agent_reviews": [asdict(review) for review in (agent_reviews or [])],
            "stage_notes": stage_notes or {},
        }
        self.store.save_alpha_explanation(alpha_run_id, self.run_id, payload)

    def complete(self, summary: dict[str, Any], *, status: str = "completed") -> None:
        self.store.finish_pipeline_run(self.run_id, status=status, summary=summary)
        self.event("store", "INFO", "run_complete", "Pipeline run completed.", payload=summary)

    def fail(self, error_message: str, *, payload: dict[str, Any] | None = None) -> None:
        self.store.update_pipeline_run(self.run_id, status="failed", current_stage=self.current_stage)
        self.event(self.current_stage, "ERROR", "run_failed", error_message, payload=payload)
