from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import json
import re
import sqlite3
import subprocess
import sys
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import yaml

from config import AppConfig, load_config
from database import AlphaStore
from dashboard.theory_catalog import THEORY_CATALOG
from api_layer.session_manager import WQSessionManager
from pipeline.alpha_pipeline import AlphaPipeline
from pipeline.generator.expression_validator import ExpressionValidator
from pipeline.models import (
    AlphaCandidate,
    AgentReview,
    SimulationMetrics,
    aggregate_stage_verdict,
    average_stage_confidence,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SPACES = re.compile(r"\s+")
TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?")
STRATEGY_OPTIONS = ["momentum", "mean_reversion", "volume"]
UNIVERSE_OPTIONS = ["TOP3000", "TOP2000", "TOP1000", "TOP500", "TOP200"]
NEUTRALIZATION_OPTIONS = ["NONE", "MARKET", "SECTOR", "INDUSTRY", "SUBINDUSTRY"]
FIELD_EXPLANATIONS = {
    "returns": {"description": "Daily close-to-close return.", "type": "MATRIX", "source": "Brain built-in"},
    "close": {"description": "Daily close price.", "type": "MATRIX", "source": "Brain built-in"},
    "volume": {"description": "Daily traded volume.", "type": "MATRIX", "source": "Brain built-in"},
    "vwap": {"description": "Volume-weighted average price.", "type": "MATRIX", "source": "Brain built-in"},
}
OPERATOR_EXPLANATIONS = {
    "rank": {"definition": "Cross-sectional rank of x.", "reason": "Robust ordering and outlier control."},
    "ts_mean": {"definition": "Rolling mean over d periods.", "reason": "Smooths noise and usually lowers turnover."},
    "ts_delta": {"definition": "Difference from value d periods ago.", "reason": "Measures displacement and directional pressure."},
    "ts_std_dev": {"definition": "Rolling standard deviation.", "reason": "Normalizes by local volatility."},
    "ts_corr": {"definition": "Rolling correlation of two series.", "reason": "Captures interaction and confirmation effects."},
    "zscore": {"definition": "Cross-sectional standard score.", "reason": "Puts values on a comparable scale."},
}


class RunRequest(BaseModel):
    strategy_type: str = "momentum"
    count: int | None = None
    dry_run: bool = False
    submit_enabled: bool = False
    bruteforce: bool = False
    bruteforce_skip: int = 0
    submit_bruteforce: bool = False


class TheoryPayload(BaseModel):
    theory_id: str
    domain: str
    title: str
    sector_tags: list[str] = Field(default_factory=list)
    core_principle: str
    alpha_implication: list[str] = Field(default_factory=list)
    example_expression: str
    agent_reasoning: list[str] = Field(default_factory=list)
    source: str = "ui"
    status: str = "active"
    created_by: str = "ui"


class SettingsPayload(BaseModel):
    worldquant_username: str = ""
    worldquant_password: str = ""
    openrouter_api_key: str = ""
    alphas_per_run: int = 10
    region: str = "USA"
    universe: str = "TOP3000"
    neutralization: str = "SUBINDUSTRY"
    auto_submit: bool = False
    sim_throttle: int = 5
    max_daily_submissions: int = 1
    self_critique_rounds: int = 2
    enable_research: bool = True
    custom_research_prompt: str = ""


class SettingsPatchPayload(BaseModel):
    worldquant_username: str | None = None
    worldquant_password: str | None = None
    openrouter_api_key: str | None = None
    alphas_per_run: int | None = None
    region: str | None = None
    universe: str | None = None
    neutralization: str | None = None
    auto_submit: bool | None = None
    sim_throttle: int | None = None
    max_daily_submissions: int | None = None
    self_critique_rounds: int | None = None
    enable_research: bool | None = None
    custom_research_prompt: str | None = None


class SettingsTestRequest(BaseModel):
    provider: str
    worldquant_username: str | None = None
    worldquant_password: str | None = None
    openrouter_api_key: str | None = None


class StudioContextRequest(BaseModel):
    strategy_type: str = "momentum"
    focus_query: str = ""


class StudioGenerateRequest(BaseModel):
    target: str = "Both"
    strategy_type: str = "momentum"
    objective: str = "Fitness-first"
    count: int = 8
    context: str = ""


class StudioQueryRequest(BaseModel):
    target: str = "Both"
    prompt: str


class StudioSimulateRequest(BaseModel):
    expression: str
    strategy_type: str = "momentum"
    metadata: dict[str, Any] = Field(default_factory=dict)
    review_context: str = ""


def canonicalize(expression: str) -> str:
    return CANONICAL_SPACES.sub("", expression.strip())


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return load_config(ROOT)


@lru_cache(maxsize=1)
def get_store() -> AlphaStore:
    return AlphaStore(get_config().alpha_store_path)


@lru_cache(maxsize=1)
def get_pipeline() -> AlphaPipeline:
    return AlphaPipeline(get_config())


@lru_cache(maxsize=1)
def get_validator() -> ExpressionValidator:
    return ExpressionValidator()


def reset_runtime_cache() -> None:
    get_config.cache_clear()
    get_store.cache_clear()
    get_pipeline.cache_clear()
    get_validator.cache_clear()


def db_connect(config: AppConfig) -> sqlite3.Connection:
    conn = sqlite3.connect(config.alpha_store_path)
    conn.row_factory = sqlite3.Row
    return conn


def latest_log_files(root: Path, limit: int = 30) -> list[Path]:
    log_root = root / "logs"
    if not log_root.exists():
        return []
    return sorted((path for path in log_root.rglob("*") if path.is_file()), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def tail_file(path: Path | None, limit: int = 120) -> list[str]:
    if path is None or not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    return lines[-limit:]


def find_primary_log(root: Path) -> Path | None:
    files = latest_log_files(root, limit=50)
    preferred = [path for path in files if "bruteforce" in str(path).lower() or "react_ui" in str(path).lower()]
    return (preferred or files or [None])[0]


def parse_progress(
    lines: list[str],
    run: dict[str, Any] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    stages = {
        "Research": {"status": "pending", "detail": "Pending"},
        "Generate": {"status": "pending", "detail": "Pending"},
        "Pre-backtest": {"status": "pending", "detail": "Pending"},
        "Simulate": {"status": "pending", "detail": "Pending"},
        "Filter": {"status": "pending", "detail": "Pending"},
        "Submit": {"status": "pending", "detail": "Pending"},
        "Store": {"status": "pending", "detail": "Pending"},
    }
    run_number = 0
    total = 0
    done = 0
    recent_events = events or []

    if run:
        stage_order = ["research", "generate", "pre_backtest", "simulate", "filter", "submit", "store"]
        stage_titles = {
            "research": "Research",
            "generate": "Generate",
            "pre_backtest": "Pre-backtest",
            "simulate": "Simulate",
            "filter": "Filter",
            "submit": "Submit",
            "store": "Store",
        }
        current_stage = str(run.get("current_stage") or "").lower()
        run_status = str(run.get("status") or "").lower()
        try:
            raw_summary = json.loads(str(run.get("summary_json") or "{}"))
        except json.JSONDecodeError:
            raw_summary = {}
        for name in stage_order:
            title = stage_titles[name]
            if not current_stage:
                continue
            if stage_order.index(name) < stage_order.index(current_stage):
                stages[title] = {"status": "done", "detail": "Done"}
            elif name == current_stage:
                detail = "Failed" if run_status == "failed" else ("Done" if run_status == "completed" and name == "store" else "Running")
                stages[title] = {"status": "error" if run_status == "failed" else ("done" if detail == "Done" else "running"), "detail": detail}
        if run_status == "completed":
            for title in stages:
                if stages[title]["status"] == "pending":
                    stages[title] = {"status": "done", "detail": "Done"}
        if run_status == "completed" and int(raw_summary.get("tested") or 0) == 0:
            screened_out = int(raw_summary.get("pre_backtest_screened_out") or 0)
            if screened_out > 0:
                stages["Pre-backtest"] = {"status": "done", "detail": f"{screened_out} blocked"}
                stages["Simulate"] = {"status": "pending", "detail": "Skipped after pre-backtest"}
            else:
                stages["Simulate"] = {"status": "error", "detail": "No simulation output"}
            stages["Filter"] = {"status": "pending", "detail": "Skipped"}
            stages["Submit"] = {"status": "pending", "detail": "Skipped"}
            stages["Store"] = {"status": "done", "detail": "Stored summary only"}

    alpha_results = [event for event in recent_events if event.get("event_type") == "candidate_result"]
    if alpha_results:
        done = len(alpha_results)
        total = max(done, int((run or {}).get("target_count") or 0))
        stages["Simulate"] = {"status": "done" if done >= total and total else "running", "detail": f"{done}/{max(total, done)} done"}

    fail_event = next((event for event in recent_events if event.get("event_type") == "run_failed"), None)
    if fail_event:
        current_stage = str(fail_event.get("stage") or (run or {}).get("current_stage") or "research").capitalize()
        if current_stage in stages:
            stages[current_stage] = {"status": "error", "detail": "Failed"}

    for line in lines:
        lower = line.lower()
        if "research" in lower:
            if stages["Research"]["status"] == "pending":
                stages["Research"] = {"status": "done", "detail": "Done"}
        if "generated" in lower or "generate" in lower:
            if stages["Generate"]["status"] == "pending":
                stages["Generate"] = {"status": "done", "detail": "Generated"}
        if "prebacktest" in lower or "pre-backtest" in lower or "proxy backtest" in lower:
            if stages["Pre-backtest"]["status"] == "pending":
                stages["Pre-backtest"] = {"status": "running", "detail": "Ranking"}
        match = re.search(r"progress\s+(\d+)/(\d+)", lower)
        if match:
            done = max(done, int(match.group(1)))
            total = max(total, int(match.group(2)))
            stages["Simulate"] = {"status": "running", "detail": f"{done}/{total} done"}
        if "quality gate" in lower or "candidate finished" in lower or "gate_fail" in lower or "gate_warning" in lower:
            if stages["Filter"]["status"] == "pending":
                stages["Filter"] = {"status": "running", "detail": "Evaluating"}
        if "attempting submission" in lower or "submit_attempt" in lower or "submitting brute-force winner" in lower:
            stages["Submit"] = {"status": "running", "detail": "Submitting"}
        if "saved to db" in lower or "store" in lower:
            if stages["Store"]["status"] == "pending":
                stages["Store"] = {"status": "done", "detail": "Stored"}
        run_match = re.search(r"run\s*#?(\d+)", lower)
        if run_match:
            run_number = max(run_number, int(run_match.group(1)))
    if total and done >= total:
        stages["Simulate"] = {"status": "done", "detail": f"{done}/{total} done"}
        if stages["Filter"]["status"] == "pending":
            stages["Filter"] = {"status": "done", "detail": "Done"}
    return {"run_number": run_number, "done": done, "total": total, "stages": stages}


def compute_notifications(rows: list[dict[str, Any]], config: AppConfig) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    store = get_store()
    approved = [row for row in rows if row["status"] == "approved"]
    if approved:
        best = max(approved, key=lambda row: float(row.get("fitness") or 0.0))
        remaining = max(config.settings["worldquant"]["daily_submit_limit"] - store.daily_submission_count(), 0)
        alerts.append(
            {
                "kind": "warning",
                "title": "Alpha ready to submit",
                "body": (
                    f"Alpha #{best['id']} has Sharpe {float(best.get('sharpe') or 0.0):.2f} and "
                    f"Fitness {float(best.get('fitness') or 0.0):.2f}. Remaining daily submissions: {remaining}."
                ),
            }
        )
    recent_failures = [row for row in rows[:30] if "failed" in str(row.get("notes") or "").lower()]
    if recent_failures:
        alerts.append(
            {
                "kind": "error",
                "title": "Recent simulation failures",
                "body": f"{len(recent_failures)} recent rows contain simulation failures or disconnects.",
            }
        )
    if rows:
        top = max(rows, key=lambda row: float(row.get("sharpe") or 0.0))
        alerts.append(
            {
                "kind": "success",
                "title": "Best recent alpha",
                "body": f"Alpha #{top['id']} currently leads with Sharpe {float(top.get('sharpe') or 0.0):.2f}.",
            }
        )
    return alerts


def build_activity_feed_from_events(events: list[dict[str, Any]], limit: int = 18) -> list[dict[str, str]]:
    feed: list[dict[str, str]] = []
    for event in reversed(events[:limit]):
        timestamp = str(event.get("created_at") or "")[11:19]
        icon = str(event.get("event_type") or "event").upper()
        message = str(event.get("message") or "")
        if event.get("alpha_expression"):
            message = f"{message} [{event['alpha_expression']}]"
        feed.append({"timestamp": timestamp, "icon": icon, "message": message})
    return feed


def format_event_label(value: str) -> str:
    return str(value).replace("_", " ").strip().title()


def simulation_queue_state(root: Path) -> dict[str, Any]:
    queue_dir = root / "runtime" / "simulation_fifo"
    if not queue_dir.exists():
        return {"active": None, "waiting": [], "count": 0}
    active_lock = queue_dir / "active.lock"
    active: dict[str, Any] | None = None
    if active_lock.exists():
        try:
            payload = json.loads(active_lock.read_text(encoding="utf-8", errors="ignore") or "{}")
        except json.JSONDecodeError:
            payload = {"ticket": active_lock.read_text(encoding="utf-8", errors="ignore").strip()}
        acquired_at = float(payload.get("acquired_at") or 0.0)
        active = {
            "ticket": payload.get("ticket"),
            "expression": payload.get("expression"),
            "waiting_seconds": max(0, int(time.time() - acquired_at)) if acquired_at else None,
        }
    waiting: list[dict[str, Any]] = []
    for ticket in sorted(queue_dir.glob("*.ticket"), key=lambda path: path.name)[:8]:
        try:
            expression = ticket.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            expression = ""
        waiting.append(
            {
                "ticket": ticket.name,
                "expression": expression,
                "queued_at": ticket.stat().st_mtime,
            }
        )
    return {"active": active, "waiting": waiting, "count": len(waiting) + (1 if active else 0)}


def theory_basis_for_run(store: AlphaStore, run_id: str | None, strategy_type: str | None) -> list[dict[str, Any]]:
    theories = [normalize_theory_row(item) for item in store.list_theory_entries(limit=400)]
    theory_map = {item["id"]: item for item in theories}
    counts: Counter[str] = Counter()
    if run_id:
        for row in store.list_alpha_explanations(run_id=run_id, limit=40):
            explanation = parse_explanation_row(row)
            if explanation is None:
                continue
            for theory_id in explanation.get("theory_ids_json", [])[:6]:
                if theory_id in theory_map:
                    counts[theory_id] += 1
    if counts:
        ranked = []
        for theory_id, count in counts.most_common(4):
            theory = theory_map[theory_id]
            ranked.append(
                {
                    "title": theory["title"],
                    "reason": theory["core_principle"],
                    "count": count,
                    "source": "linked_to_generated_alpha",
                }
            )
        return ranked

    lower_strategy = str(strategy_type or "").replace("_", " ").lower()
    fallback: list[dict[str, Any]] = []
    for theory in theories:
        haystack = f"{theory['title']} {theory['core_principle']}".lower()
        if lower_strategy and lower_strategy.split()[0] in haystack:
            fallback.append(
                {
                    "title": theory["title"],
                    "reason": theory["core_principle"],
                    "count": 0,
                    "source": "strategy_default",
                }
            )
        elif "order statistics" in haystack or "liquidity" in haystack:
            fallback.append(
                {
                    "title": theory["title"],
                    "reason": theory["core_principle"],
                    "count": 0,
                    "source": "strategy_default",
                }
            )
        if len(fallback) >= 4:
            break
    return fallback[:4]


def workflow_task_timeline(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = list(reversed(events))
    timeline: list[dict[str, Any]] = []
    for event in ordered[-14:]:
        label = format_event_label(str(event.get("event_type") or "event"))
        detail = str(event.get("message") or "")
        alpha_expression = event.get("alpha_expression")
        payload = event.get("payload") or {}
        if event.get("event_type") == "candidate_started" and alpha_expression:
            detail = f"Waiting to simulate {alpha_expression}"
        elif event.get("event_type") == "candidate_generation":
            detail = str(event.get("message") or "")
        elif event.get("event_type") == "candidate_dedup":
            detail = str(event.get("message") or "")
        elif event.get("event_type") == "prebacktest_ranked":
            label = "Pre-backtest ranking"
        elif event.get("event_type") == "prebacktest_promoted" and alpha_expression:
            label = "Pre-backtest promoted"
            detail = f"Promoted for live simulation: {alpha_expression}"
        elif event.get("event_type") == "prebacktest_blocked" and alpha_expression:
            label = "Pre-backtest blocked"
            detail = f"Blocked before live simulation: {alpha_expression}"
        elif event.get("event_type") == "stage":
            label = f"{format_event_label(str(event.get('stage') or 'stage'))} stage"
        elif event.get("event_type") == "run_failed":
            label = "Run failed"
        elif event.get("event_type") == "run_complete":
            label = "Run completed"
        if payload.get("metadata") and isinstance(payload["metadata"], dict):
            family = payload["metadata"].get("family")
            if family and "family=" not in detail.lower():
                detail = f"{detail} Family {family}."
        timeline.append(
            {
                "timestamp": str(event.get("created_at") or ""),
                "stage": str(event.get("stage") or ""),
                "status": str(event.get("level") or "INFO").lower(),
                "label": label,
                "detail": detail,
                "alpha_expression": alpha_expression,
            }
        )
    return timeline[-10:]


def build_workflow_detail(root: Path, store: AlphaStore, latest_run: dict[str, Any] | None, latest_events: list[dict[str, Any]]) -> dict[str, Any]:
    run_id = str((latest_run or {}).get("run_id") or "")
    strategy_type = str((latest_run or {}).get("strategy_type") or "")
    research_items = [serialize_research_artifact(item) for item in store.list_research_artifacts(run_id=run_id, limit=6)] if run_id else []
    queue = simulation_queue_state(root)
    latest_task = workflow_task_timeline(latest_events)[-1] if latest_events else None
    current_alpha = None
    if queue.get("active") and queue["active"].get("expression"):
        current_alpha = queue["active"]["expression"]
    else:
        for event in reversed(latest_events):
            if event.get("alpha_expression"):
                current_alpha = str(event["alpha_expression"])
                break
    return {
        "current_task": latest_task,
        "current_alpha": current_alpha,
        "simulation_queue": queue,
        "task_timeline": workflow_task_timeline(latest_events),
        "research_basis": [
            {
                "title": str(item.get("title") or item.get("kind") or "Research artifact"),
                "kind": str(item.get("kind") or ""),
                "query_text": str(item.get("query_text") or ""),
                "created_at": str(item.get("created_at") or ""),
            }
            for item in research_items
        ],
        "theory_basis": theory_basis_for_run(store, run_id, strategy_type),
    }


def build_histogram(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = {"< 0": 0, "0-0.5": 0, "0.5-1": 0, "1-1.5": 0, "> 1.5": 0}
    for row in rows:
        sharpe = float(row.get("sharpe") or 0.0)
        if sharpe < 0:
            buckets["< 0"] += 1
        elif sharpe < 0.5:
            buckets["0-0.5"] += 1
        elif sharpe < 1.0:
            buckets["0.5-1"] += 1
        elif sharpe < 1.5:
            buckets["1-1.5"] += 1
        else:
            buckets["> 1.5"] += 1
    return [{"bucket": bucket, "count": count} for bucket, count in buckets.items()]


def parse_expression_features(expression: str) -> dict[str, Any]:
    expr = expression.lower()
    fields = sorted({token for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr) if token in FIELD_EXPLANATIONS})
    operators = sorted({token for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr) if token in OPERATOR_EXPLANATIONS})
    if "ts_corr(volume" in expr:
        theme = "Liquidity-confirmed momentum"
        hypothesis = "Order flow and return are moving together, so participation may still be reinforcing direction."
    elif "volume / ts_mean(volume" in expr:
        theme = "Liquidity regime shift"
        hypothesis = "Sustained abnormal volume may signal a structural participation change rather than one-day noise."
    elif "-ts_delta(vwap" in expr or "-ts_delta(close" in expr:
        theme = "Short-term reversal"
        hypothesis = "Recent losers may bounce if the market overreacted or if panic flow is fading."
    elif "close / ts_mean(close" in expr:
        theme = "Price versus local anchor"
        hypothesis = "Distance from a rolling mean can encode anchoring, drift, or mean reversion pressure."
    elif "ts_delta(close" in expr and "ts_std_dev" in expr:
        theme = "Volatility-normalized trend"
        hypothesis = "Directional movement matters most when it survives scaling by local volatility."
    else:
        theme = "Return persistence"
        hypothesis = "Recent return leadership may persist if information diffuses gradually across the universe."
    return {"fields": fields, "operators": operators, "theme": theme, "hypothesis": hypothesis}


def explain_data_fields(fields: list[str]) -> list[dict[str, str]]:
    return [{"field": field, **FIELD_EXPLANATIONS.get(field, {"description": "-", "type": "-", "source": "-"})} for field in fields]


def explain_operators(operators: list[str]) -> list[dict[str, str]]:
    return [{"operator": operator, **OPERATOR_EXPLANATIONS.get(operator, {"definition": "-", "reason": "-"})} for operator in operators]


def normalize_inline_text(value: str, limit: int = 320) -> str:
    compact = " ".join(str(value or "").split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3].rstrip()}..."


def default_quality_thresholds() -> dict[str, float]:
    return {
        "sharpe_min": 1.0,
        "fitness_min": 1.0,
        "turnover_min": 0.01,
        "turnover_max": 0.8,
        "drawdown_max": 0.2,
        "self_correlation_max": 0.7,
    }


def build_expected_metrics(thresholds: dict[str, float] | None = None) -> dict[str, str]:
    values = {**default_quality_thresholds(), **(thresholds or {})}
    return {
        "Sharpe": f">= {values['sharpe_min']}",
        "Fitness": f">= {values['fitness_min']}",
        "Turnover": f"{values['turnover_min']} - {values['turnover_max']}",
        "Drawdown": f"<= {values['drawdown_max']}",
        "Self correlation": f"<= {values['self_correlation_max']}",
    }


def default_risks(theme: str) -> list[str]:
    risks = [
        "High self-correlation can still block submission even when Sharpe looks good.",
        "Turnover above the fitness floor can erase otherwise attractive signal quality.",
    ]
    lower = theme.lower()
    if "reversal" in lower:
        risks.append("Short-term reversal motifs can break during strong trend regimes.")
    if "momentum" in lower:
        risks.append("Momentum-style motifs can crowd quickly and decay when flows reverse.")
    if "liquidity" in lower:
        risks.append("Liquidity-linked motifs can change character around stress or event clusters.")
    return risks


def theory_ids_for_expression(expression: str, theories: list[dict[str, Any]] | None = None) -> list[str]:
    source = theories or THEORY_CATALOG
    return [item["id"] for item in match_theories(expression, source)]


def build_alpha_explanation_payload(
    expression: str,
    *,
    prompt_context: str = "",
    thresholds: dict[str, float] | None = None,
    research_refs: list[dict[str, Any]] | None = None,
    agent_reviews: list[dict[str, Any]] | None = None,
    stage_notes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    features = parse_expression_features(expression)
    return {
        "theme": features["theme"],
        "hypothesis": features["hypothesis"],
        "prompt_context": prompt_context[:5000],
        "expected_metrics": build_expected_metrics(thresholds),
        "risks": default_risks(features["theme"]),
        "theory_ids": theory_ids_for_expression(expression),
        "research_refs": research_refs or [],
        "field_info": explain_data_fields(features["fields"]),
        "operator_info": explain_operators(features["operators"]),
        "agent_reviews": agent_reviews or [],
        "stage_notes": stage_notes or {},
    }


def build_alpha_analysis(
    row: dict[str, Any],
    explanation: dict[str, Any],
    matched_theories: list[dict[str, Any]],
    research: list[dict[str, Any]],
    related_documents: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics_line = (
        f"Observed metrics: Sharpe {float(row.get('sharpe') or 0.0):.2f}, "
        f"Fitness {float(row.get('fitness') or 0.0):.2f}, "
        f"Turnover {float(row.get('turnover') or 0.0):.2%}."
    )
    creation_reason = normalize_inline_text(
        explanation.get("prompt_context")
        or row.get("rationale")
        or explanation.get("hypothesis")
        or f"Alpha was created to test the {explanation.get('theme', 'current')} motif."
    )

    evidence_basis: list[str] = []
    fields = [str(item.get("field")) for item in explanation.get("field_info_json", []) if item.get("field")]
    operators = [str(item.get("operator")) for item in explanation.get("operator_info_json", []) if item.get("operator")]
    if fields:
        evidence_basis.append(f"Data fields used: {', '.join(fields)}.")
    if operators:
        evidence_basis.append(f"Operators used: {', '.join(operators)}.")
    evidence_basis.append(metrics_line)
    pre_backtest = explanation.get("stage_notes_json", {}).get("pre_backtest") or row.get("pre_backtest_metrics_json") or {}
    estimated = pre_backtest.get("estimated_metrics") if isinstance(pre_backtest, dict) else None
    if estimated:
        evidence_basis.append(
            "Local proxy backtest before Brain simulate: "
            f"Sharpe {float(estimated.get('sharpe') or 0.0):.2f}, "
            f"Fitness {float(estimated.get('fitness') or 0.0):.2f}, "
            f"Return {float(estimated.get('annual_returns') or 0.0):.2%}."
        )
    for artifact in research[:2]:
        evidence_basis.append(f"Research artifact: {normalize_inline_text(str(artifact.get('title') or 'Untitled artifact'))}.")
    for doc in related_documents[:2]:
        evidence_basis.append(
            f"Knowledge-base reference: {Path(str(doc.get('path') or '')).name} (match score {doc.get('score', 0)})."
        )

    theory_basis = [
        f"{item['title']}: {normalize_inline_text(item['core_principle'], 180)}"
        for item in matched_theories[:4]
    ]
    if not theory_basis and explanation.get("theme"):
        theory_basis.append(f"Fallback theme: {explanation['theme']}.")

    implementation_logic = [normalize_inline_text(str(explanation.get("hypothesis") or ""))]
    for item in explanation.get("operator_info_json", [])[:3]:
        operator = str(item.get("operator") or "")
        reason = normalize_inline_text(str(item.get("reason") or item.get("definition") or ""), 160)
        if operator and reason:
            implementation_logic.append(f"{operator}: {reason}")

    confidence_notes = [normalize_inline_text(str(item), 200) for item in explanation.get("risks_json", [])[:4]]
    gate_reasons = explanation.get("stage_notes_json", {}).get("gate_reasons", [])
    if isinstance(pre_backtest, dict) and pre_backtest.get("score") is not None:
        confidence_notes.append(
            f"Local proxy backtest score: {float(pre_backtest.get('score') or 0.0):.2f} "
            f"({'promoted' if pre_backtest.get('promoted') else 'not promoted'})."
        )
    for reason in gate_reasons[:3]:
        confidence_notes.append(f"Gate note: {normalize_inline_text(str(reason), 180)}")
    if row.get("pre_sim_verdict"):
        confidence_notes.append(
            f"Pre-simulation review: {row.get('pre_sim_verdict')} at confidence {float(row.get('pre_sim_confidence') or 0.0):.2f}."
        )
    if row.get("post_sim_verdict"):
        confidence_notes.append(
            f"Post-simulation review: {row.get('post_sim_verdict')} at confidence {float(row.get('post_sim_confidence') or 0.0):.2f}."
        )
    if not confidence_notes:
        confidence_notes.append("No explicit risk note was stored for this alpha.")

    return {
        "creation_reason": creation_reason,
        "evidence_basis": evidence_basis,
        "theory_basis": theory_basis,
        "implementation_logic": implementation_logic,
        "confidence_notes": confidence_notes,
    }


def normalize_theory_row(row: dict[str, Any]) -> dict[str, Any]:
    def _parse(payload: str, fallback: list[str]) -> list[str]:
        try:
            return json.loads(str(payload))
        except json.JSONDecodeError:
            return fallback

    return {
        "id": row["theory_id"],
        "domain": row["domain"],
        "title": row["title"],
        "sector_tags": _parse(row["sector_tags_json"], []),
        "core_principle": row["core_principle"],
        "alpha_implication": _parse(row["alpha_implication_json"], []),
        "example_expression": row["example_expression"],
        "agent_reasoning": _parse(row["agent_reasoning_json"], []),
        "source": row["source"],
        "status": row["status"],
        "version": row["version"],
        "created_by": row["created_by"],
        "updated_at": row["updated_at"],
    }


def match_theories(expression: str, theories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expr = expression.lower()
    matched: list[dict[str, Any]] = []
    for theory in theories:
        title = theory["title"].lower()
        if "reversion" in title and ("-ts_delta" in expr or ("close / ts_mean" in expr and "- 1" in expr)):
            matched.append(theory)
        elif "momentum" in title and ("ts_mean(returns" in expr or "ts_delta(close" in expr):
            matched.append(theory)
        elif "liquidity" in title and "volume" in expr:
            matched.append(theory)
        elif "microstructure" in title and "volume" in expr:
            matched.append(theory)
        elif "order statistics" in title and "rank(" in expr:
            matched.append(theory)
        elif "garch" in title and "ts_std_dev" in expr:
            matched.append(theory)
        elif "anchoring" in title and "close / ts_mean(close" in expr:
            matched.append(theory)
        elif "entropy" in title and "vwap" in expr:
            matched.append(theory)
    unique = {item["id"]: item for item in matched}
    return list(unique.values())[:4]


def find_relevant_documents(root: Path, query: str, limit: int = 6) -> list[dict[str, Any]]:
    files = [
        path
        for path in (root / "knowledge_base").rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}
    ]
    query_tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query.lower()))
    scored: list[tuple[int, Path]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        sample = f"{path.name} {path.parent.name} {text[:4000]}".lower()
        score = len(query_tokens & set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sample)))
        if score > 0:
            scored.append((score, path))
    scored.sort(key=lambda item: item[0], reverse=True)
    results: list[dict[str, Any]] = []
    for score, path in scored[:limit]:
        excerpt = path.read_text(encoding="utf-8", errors="ignore")[:2600]
        results.append({"path": str(path), "score": score, "excerpt": excerpt})
    return results


def recent_research_files(limit: int = 10) -> list[str]:
    files = [
        path
        for path in (ROOT / "knowledge_base").rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}
    ]
    return [str(path) for path in sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]]


def latest_simulated_report(root: Path) -> dict[str, Any] | None:
    files = sorted(
        (root / "knowledge_base" / "generated_alpha_only" / "simulated").glob("*.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return None
    text = files[0].read_text(encoding="utf-8", errors="ignore")
    return {"path": str(files[0]), "text": text}


def load_context_bundle(
    pipeline: AlphaPipeline,
    strategy_type: str,
    focus_query: str,
) -> dict[str, str]:
    research_digest = pipeline.daily_researcher.refresh()
    pipeline.knowledge_base.load_all()
    research_summary = pipeline._research_market(strategy_type)
    context = pipeline._build_context(strategy_type, research_summary, research_digest)
    focused_context = pipeline.knowledge_base.query_context(focus_query, k=4) if focus_query else ""
    return {
        "strategy_type": strategy_type,
        "focus_query": focus_query,
        "research_summary": research_summary,
        "focused_context": focused_context,
        "context": f"{context}\n\nFocused context:\n{focused_context}",
    }


def query_agents(pipeline: AlphaPipeline, target: str, prompt: str) -> dict[str, str]:
    responses: dict[str, str] = {}
    if target in {"Hermes", "Both"}:
        responses["Hermes"] = pipeline.hermes.ask(prompt).strip()
    if target in {"DeerFlow", "Both"}:
        responses["DeerFlow"] = pipeline.deerflow.run_research(prompt).strip()
    return responses


def extract_expressions(raw_text: str, validator: ExpressionValidator) -> list[dict[str, Any]]:
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for line in raw_text.splitlines():
        expr = line.strip().strip("- ").strip()
        if "rank(" not in expr:
            continue
        key = canonicalize(expr)
        if key in seen:
            continue
        errors = validator.validate(expr)
        items.append({"expression": expr, "valid": not errors, "errors": errors})
        seen.add(key)
    return items


def create_candidate(expression: str, strategy_type: str, metadata: dict[str, Any]) -> AlphaCandidate:
    return AlphaCandidate(
        expression=expression,
        source="react_ui",
        strategy_type=strategy_type,
        rationale="Created from WQ Brain Alpha Monitor.",
        metadata={"generation_source": "studio_manual", "origin_agent": metadata.get("origin_agent", "studio"), **metadata.copy()},
    )


def serialize_metrics(metrics: SimulationMetrics) -> dict[str, Any]:
    return asdict(metrics)


def serialize_review(review: AgentReview) -> dict[str, Any]:
    return asdict(review)


def simulate_candidate(
    pipeline: AlphaPipeline,
    validator: ExpressionValidator,
    expression: str,
    strategy_type: str,
    metadata: dict[str, Any],
    review_context: str,
) -> dict[str, Any]:
    candidate = create_candidate(expression, strategy_type, metadata)
    validation_errors = validator.validate(expression)
    history = pipeline.store.list_recent(limit=300)
    pre_backtest = pipeline.local_backtester.evaluate(candidate, history) if not validation_errors else None
    pre_reviews = [
        pipeline.hermes.review_alpha(candidate, "pre_simulation", review_context),
        pipeline.deerflow.review_alpha(candidate, "pre_simulation", review_context),
    ]
    alpha_run_id: int | None = None
    thresholds = getattr(pipeline.quality_gate, "thresholds", default_quality_thresholds())
    if validation_errors:
        metrics = SimulationMetrics(0.0, 0.0, 0.0, 0.0, 1.0, 1.0, notes="Validation failed before simulation.")
        gate_reasons = validation_errors
        status = "invalid"
        post_reviews: list[AgentReview] = []
        notes = "; ".join(gate_reasons + [f"{review.agent}:{review.stage}:{review.verdict}" for review in pre_reviews])
        alpha_run_id = pipeline.store.insert_alpha(
            candidate,
            metrics,
            status,
            notes=notes,
            rationale=review_context or candidate.rationale,
            metadata=metadata,
            agent_reviews=[serialize_review(review) for review in pre_reviews],
            generation_source=str(candidate.metadata.get("generation_source") or candidate.source),
            origin_agent=str(candidate.metadata.get("origin_agent") or "studio"),
            pre_sim_confidence=average_stage_confidence(pre_reviews, "pre_simulation"),
            pre_sim_verdict=aggregate_stage_verdict(pre_reviews, "pre_simulation"),
            run_tags={"workflow_type": "studio_simulation", "strategy_type": strategy_type, "source": "studio"},
            pre_backtest_score=float(pre_backtest.score) if pre_backtest is not None else None,
            pre_backtest_passed=bool(pre_backtest.passed) if pre_backtest is not None else None,
            pre_backtest_metrics=pipeline.local_backtester.as_payload(pre_backtest).get("estimated_metrics", {}) if pre_backtest is not None else {},
        )
    elif not pre_backtest.passed:
        metrics = pipeline._pre_backtest_metrics(pre_backtest)
        gate_reasons = list(pre_backtest.reasons)
        status = "screened_out"
        post_reviews = []
        notes = "; ".join(gate_reasons + [f"{review.agent}:{review.stage}:{review.verdict}" for review in pre_reviews])
        alpha_run_id = pipeline.store.insert_alpha(
            candidate,
            metrics,
            status,
            notes=notes,
            rationale=review_context or candidate.rationale,
            metadata=metadata,
            agent_reviews=[serialize_review(review) for review in pre_reviews],
            generation_source=str(candidate.metadata.get("generation_source") or candidate.source),
            origin_agent=str(candidate.metadata.get("origin_agent") or "studio"),
            pre_sim_confidence=average_stage_confidence(pre_reviews, "pre_simulation"),
            pre_sim_verdict=aggregate_stage_verdict(pre_reviews, "pre_simulation"),
            run_tags={"workflow_type": "studio_simulation", "strategy_type": strategy_type, "source": "studio"},
            gate_failure_reason=gate_reasons[0] if gate_reasons else None,
            pre_backtest_score=float(pre_backtest.score),
            pre_backtest_passed=bool(pre_backtest.passed),
            pre_backtest_metrics=pipeline.local_backtester.as_payload(pre_backtest).get("estimated_metrics", {}),
        )
    else:
        metrics = pipeline.simulator.run(candidate)
        metrics.self_correlation = max(
            metrics.self_correlation,
            pipeline.correlation_checker.estimate_self_correlation(candidate, history),
        )
        gate_reasons = pipeline.quality_gate.evaluate(metrics)
        status = "approved" if not gate_reasons else "tested"
        post_reviews = [
            pipeline.hermes.review_alpha(candidate, "post_simulation", review_context, metrics),
            pipeline.deerflow.review_alpha(candidate, "post_simulation", review_context, metrics),
        ]
        notes = "; ".join(gate_reasons + [f"{review.agent}:{review.stage}:{review.verdict}" for review in pre_reviews + post_reviews])
        alpha_run_id = pipeline.store.insert_alpha(
            candidate,
            metrics,
            status,
            notes=notes,
            rationale=candidate.rationale,
            metadata=metadata,
            agent_reviews=[serialize_review(review) for review in pre_reviews + post_reviews],
            generation_source=str(candidate.metadata.get("generation_source") or candidate.source),
            origin_agent=str(candidate.metadata.get("origin_agent") or "studio"),
            pre_sim_confidence=average_stage_confidence(pre_reviews, "pre_simulation"),
            post_sim_confidence=average_stage_confidence(post_reviews, "post_simulation"),
            pre_sim_verdict=aggregate_stage_verdict(pre_reviews, "pre_simulation"),
            post_sim_verdict=aggregate_stage_verdict(post_reviews, "post_simulation"),
            run_tags={"workflow_type": "studio_simulation", "strategy_type": strategy_type, "source": "studio"},
            pre_backtest_score=float(pre_backtest.score),
            pre_backtest_passed=bool(pre_backtest.passed),
            pre_backtest_metrics=pipeline.local_backtester.as_payload(pre_backtest).get("estimated_metrics", {}),
        )
    if alpha_run_id is not None:
        pipeline.store.save_alpha_explanation(
            alpha_run_id,
            None,
            build_alpha_explanation_payload(
                expression,
                prompt_context=review_context or candidate.rationale,
                thresholds=thresholds,
                agent_reviews=[serialize_review(review) for review in pre_reviews + post_reviews],
                stage_notes={
                    "status": status,
                    "pre_backtest": pipeline.local_backtester.as_payload(pre_backtest) if pre_backtest is not None else {},
                    "validation_errors": validation_errors,
                    "gate_reasons": gate_reasons,
                    "metrics": serialize_metrics(metrics),
                    "source": "studio_simulation",
                },
            ),
        )
    return {
        "alpha_run_id": alpha_run_id,
        "candidate": asdict(candidate),
        "metrics": serialize_metrics(metrics),
        "status": status,
        "validation_errors": validation_errors,
        "gate_reasons": gate_reasons,
        "pre_reviews": [serialize_review(review) for review in pre_reviews],
        "post_reviews": [serialize_review(review) for review in post_reviews],
    }


def build_generation_prompt(strategy_type: str, objective: str, count: int, context: str) -> str:
    objective_map = {
        "Fitness-first": "Optimize fitness first, then Sharpe. Favor N=20 or N=60 when signal quality is similar.",
        "Sharpe-first": "Optimize Sharpe first, but avoid noisy short-horizon duplicates.",
        "Balanced": "Balance Sharpe, fitness, drawdown control, and uniqueness.",
        "Exploration": "Explore diverse operator families and avoid duplicate motifs.",
    }
    return (
        f"Generate {count} original WorldQuant FASTEXPR alphas for {strategy_type}.\n"
        f"{objective_map.get(objective, objective_map['Balanced'])}\n"
        "You must research recent market regimes and academic papers before generating.\n"
        "Create novel expressions without using any pre-defined templates.\n"
        "Use operators such as ts_mean, ts_delta, ts_std_dev, ts_corr, rank, zscore, etc.\n"
        "Replace N with lookback from 5, 10, 20, 60.\n"
        "Return exactly one expression per line. No explanations.\n\n"
        f"Research Context:\n{context[:5000]}"
    )


def mask_secret(value: str) -> str:
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * max(len(value) - 8, 4)}{value[-4:]}"


def build_alpha_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []
    for row in rows:
        features = parse_expression_features(row["expression"])
        note_text = str(row.get("notes") or "")
        simulation_failed = bool(
            row.get("status") == "tested"
            and note_text.lower().startswith("simulation failed:")
            and float(row.get("sharpe") or 0.0) == 0.0
            and float(row.get("fitness") or 0.0) == 0.0
        )
        table.append(
            {
                "id": row["id"],
                "expression": row["expression"],
                "theme": features["theme"],
                "source": row["source"],
                "generation_source": row.get("generation_source") or row["source"],
                "origin_agent": row.get("origin_agent"),
                "strategy_type": row["strategy_type"],
                "status": row["status"],
                "sharpe": round(float(row.get("sharpe") or 0.0), 3),
                "fitness": round(float(row.get("fitness") or 0.0), 3),
                "annual_returns": round(float(row.get("annual_returns") or 0.0), 4),
                "turnover": round(float(row.get("turnover") or 0.0), 4),
                "drawdown": round(float(row.get("drawdown") or 0.0), 4),
                "self_correlation": round(float(row.get("self_correlation") or 0.0), 4),
                "pre_sim_confidence": row.get("pre_sim_confidence"),
                "post_sim_confidence": row.get("post_sim_confidence"),
                "pre_sim_verdict": row.get("pre_sim_verdict"),
                "post_sim_verdict": row.get("post_sim_verdict"),
                "pre_backtest_score": row.get("pre_backtest_score"),
                "pre_backtest_passed": row.get("pre_backtest_passed"),
                "pre_backtest_metrics": row.get("pre_backtest_metrics_json") or {},
                "simulation_failed": simulation_failed,
                "failure_note": note_text if simulation_failed else None,
                "needs_review": bool(row.get("needs_review")),
                "gate_failure_reason": row.get("gate_failure_reason"),
                "submitted_at": row.get("submitted_at"),
                "created_at": str(row.get("created_at") or "")[:19],
            }
        )
    return table


def build_similarity_matrix(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    sample = rows[:limit]
    token_sets = {
        row["id"]: set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", row["expression"].lower()))
        for row in sample
    }
    matrix: list[dict[str, Any]] = []
    for left in sample:
        left_tokens = token_sets[left["id"]]
        row_data: dict[str, Any] = {"alpha": f"#{left['id']}"}
        for right in sample:
            right_tokens = token_sets[right["id"]]
            union = left_tokens | right_tokens
            score = 1.0 if not union else len(left_tokens & right_tokens) / len(union)
            row_data[f"#{right['id']}"] = round(score, 2)
        matrix.append(row_data)
    return matrix


def domain_summary(theories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(item["domain"] for item in theories)
    return [{"domain": domain, "count": count} for domain, count in sorted(counts.items())]


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "simulated": 0,
            "passing": 0,
            "submitted": 0,
            "errors": 0,
            "average_sharpe": 0.0,
            "best_sharpe": 0.0,
        }
    simulated_rows = [row for row in rows if row.get("status") != "screened_out"]
    sharpe_values = [float(row.get("sharpe") or 0.0) for row in simulated_rows] or [0.0]
    return {
        "simulated": len(simulated_rows),
        "passing": sum(1 for row in simulated_rows if row["status"] in {"approved", "submitted"}),
        "submitted": sum(1 for row in simulated_rows if row["status"] == "submitted"),
        "errors": sum(1 for row in simulated_rows if "failed" in str(row.get("notes") or "").lower()),
        "average_sharpe": round(sum(sharpe_values) / len(sharpe_values), 3),
        "best_sharpe": round(max(sharpe_values), 3),
    }


def parse_alpha_row(row: dict[str, Any]) -> dict[str, Any]:
    parsed = dict(row)
    for key in ("metadata_json", "checks_json", "agent_reviews_json", "run_tags_json", "pre_backtest_metrics_json"):
        try:
            parsed[key] = json.loads(str(parsed.get(key) or "{}" if key in {"metadata_json", "run_tags_json", "pre_backtest_metrics_json"} else parsed.get(key) or "[]"))
        except json.JSONDecodeError:
            parsed[key] = {} if key in {"metadata_json", "run_tags_json", "pre_backtest_metrics_json"} else []
    parsed["needs_review"] = bool(parsed.get("needs_review"))
    if parsed.get("pre_backtest_passed") is not None:
        parsed["pre_backtest_passed"] = bool(parsed.get("pre_backtest_passed"))
    parsed["pre_backtest_metrics"] = parsed.get("pre_backtest_metrics_json") or {}
    return parsed


def parse_explanation_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    parsed = dict(row)
    for key in (
        "expected_metrics_json",
        "risks_json",
        "theory_ids_json",
        "research_refs_json",
        "field_info_json",
        "operator_info_json",
        "agent_reviews_json",
        "stage_notes_json",
    ):
        try:
            parsed[key] = json.loads(str(parsed.get(key) or "{}" if key in {"expected_metrics_json", "stage_notes_json"} else parsed.get(key) or "[]"))
        except json.JSONDecodeError:
            parsed[key] = {} if key in {"expected_metrics_json", "stage_notes_json"} else []
    return parsed


def slugify_reason(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return text[:80] or "unknown_reason"


def summarize_failure_patterns(store: AlphaStore, limit: int = 400) -> dict[str, Any]:
    rows = [parse_alpha_row(item) for item in store.list_recent(limit=limit)]
    events = [serialize_pipeline_event(item) for item in store.list_pipeline_events(limit=max(limit * 2, 200))]
    alpha_by_id = {int(row["id"]): row for row in rows if row.get("id") is not None}
    buckets: dict[str, dict[str, Any]] = {}
    total = 0

    for event in events:
        if event.get("event_type") not in {"GATE_FAIL", "candidate_failed", "candidate_invalid"}:
            continue
        total += 1
        payload = event.get("payload") or {}
        raw_reason = str(payload.get("reason") or event.get("message") or "unknown")
        key = slugify_reason(raw_reason)
        row = alpha_by_id.get(int(event["alpha_run_id"])) if event.get("alpha_run_id") else None
        bucket = buckets.setdefault(
            key,
            {
                "reason": key,
                "label": str(raw_reason).replace("_", " ").strip().capitalize(),
                "count": 0,
                "fields": Counter(),
                "sources": Counter(),
                "examples": [],
                "avg_sharpe_samples": [],
            },
        )
        bucket["count"] += 1
        if payload.get("field"):
            bucket["fields"][str(payload["field"])] += 1
        if row is not None:
            bucket["sources"][str(row.get("generation_source") or row.get("source") or "unknown")] += 1
            bucket["avg_sharpe_samples"].append(float(row.get("sharpe") or 0.0))
            if row.get("expression") and len(bucket["examples"]) < 3:
                bucket["examples"].append(str(row["expression"]))

    items: list[dict[str, Any]] = []
    for bucket in sorted(buckets.values(), key=lambda item: item["count"], reverse=True)[:8]:
        fields = [name for name, _ in bucket["fields"].most_common(3)]
        source_breakdown = [{"source": source, "count": count} for source, count in bucket["sources"].most_common(4)]
        avg_sharpe = (
            round(sum(bucket["avg_sharpe_samples"]) / len(bucket["avg_sharpe_samples"]), 3)
            if bucket["avg_sharpe_samples"]
            else 0.0
        )
        items.append(
            {
                "reason": bucket["reason"],
                "label": bucket["label"],
                "count": bucket["count"],
                "fields": fields,
                "sources": source_breakdown,
                "avg_sharpe": avg_sharpe,
                "examples": bucket["examples"],
            }
        )

    return {
        "items": items,
        "total_fail_events": total,
        "recent_failed_alphas": sum(1 for row in rows if row.get("status") in {"tested", "invalid"}),
    }


def summarize_theory_usage(store: AlphaStore, limit: int = 400) -> dict[str, Any]:
    theories = [normalize_theory_row(item) for item in store.list_theory_entries(limit=500)]
    rows = {int(item["id"]): parse_alpha_row(item) for item in store.list_recent(limit=limit) if item.get("id") is not None}
    usage: dict[str, dict[str, Any]] = {
        theory["id"]: {
            "theory_id": theory["id"],
            "title": theory["title"],
            "domain": theory["domain"],
            "generated": 0,
            "passing": 0,
            "submitted": 0,
            "avg_sharpe_samples": [],
        }
        for theory in theories
    }

    for item in store.list_alpha_explanations(limit=limit):
        explanation = parse_explanation_row(item)
        if explanation is None:
            continue
        alpha_row = rows.get(int(item.get("alpha_run_id") or 0))
        for theory_id in explanation.get("theory_ids_json", [])[:8]:
            if theory_id not in usage:
                continue
            record = usage[theory_id]
            record["generated"] += 1
            if alpha_row is not None:
                if alpha_row.get("status") in {"approved", "submitted"}:
                    record["passing"] += 1
                if alpha_row.get("status") == "submitted":
                    record["submitted"] += 1
                record["avg_sharpe_samples"].append(float(alpha_row.get("sharpe") or 0.0))

    items: list[dict[str, Any]] = []
    for theory_id, record in usage.items():
        generated = int(record["generated"])
        if generated <= 0:
            pass_rate = 0.0
            avg_sharpe = 0.0
        else:
            pass_rate = round(float(record["passing"]) / generated, 3)
            avg_sharpe = round(sum(record["avg_sharpe_samples"]) / max(len(record["avg_sharpe_samples"]), 1), 3)
        items.append(
            {
                "theory_id": theory_id,
                "title": record["title"],
                "domain": record["domain"],
                "generated": generated,
                "passing": int(record["passing"]),
                "submitted": int(record["submitted"]),
                "pass_rate": pass_rate,
                "avg_sharpe": avg_sharpe,
            }
        )

    ranked = sorted(items, key=lambda item: (item["generated"], item["pass_rate"], item["avg_sharpe"]), reverse=True)
    return {
        "items": ranked,
        "top": ranked[:8],
        "summary": {
            "tracked_theories": len(theories),
            "used_theories": sum(1 for item in ranked if item["generated"] > 0),
            "unused_theories": sum(1 for item in ranked if item["generated"] == 0),
        },
    }


def latest_report(config: AppConfig) -> dict[str, Any] | None:
    with db_connect(config) as conn:
        row = conn.execute(
            "SELECT id, run_id, report_date, summary_json, created_at FROM daily_reports ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    try:
        summary = json.loads(str(row["summary_json"]))
    except json.JSONDecodeError:
        summary = {}
    return {
        "id": row["id"],
        "run_id": row["run_id"],
        "report_date": row["report_date"],
        "created_at": row["created_at"],
        "summary": summary,
    }


def run_pipeline_now(payload: RunRequest) -> dict[str, Any]:
    log_name = "react_ui_bruteforce" if payload.bruteforce else "react_ui_run"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out_path = ROOT / "logs" / f"{log_name}_{stamp}.out.log"
    err_path = ROOT / "logs" / f"{log_name}_{stamp}.err.log"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, "main.py", "--run-once", "--strategy-type", payload.strategy_type]
    if payload.count is not None:
        args.extend(["--count", str(payload.count)])
    if payload.dry_run:
        args.append("--dry-run")
    if not payload.submit_enabled:
        args.append("--no-submit")
    if payload.bruteforce:
        args.append("--bruteforce")
        if payload.bruteforce_skip:
            args.extend(["--bruteforce-skip", str(payload.bruteforce_skip)])
        if payload.submit_bruteforce and payload.submit_enabled:
            args.append("--submit-bruteforce")
    process = subprocess.Popen(
        args,
        cwd=ROOT,
        stdout=out_path.open("w", encoding="utf-8"),
        stderr=err_path.open("w", encoding="utf-8"),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return {"status": "started", "pid": process.pid, "stdout_log": str(out_path), "stderr_log": str(err_path)}


def stop_pipeline_jobs() -> dict[str, Any]:
    script = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*main.py*' } | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force; $_.ProcessId }"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=20,
    )
    pids = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    return {"status": "stopped" if pids else "idle", "pids": pids}


def current_settings_payload(config: AppConfig) -> SettingsPayload:
    alpha_defaults = config.alpha_defaults
    return SettingsPayload(
        worldquant_username=config.env.get("WQ_USERNAME", ""),
        worldquant_password="",
        openrouter_api_key="",
        alphas_per_run=int(config.settings.get("pipeline", {}).get("llm_batch", 10)),
        region=str(alpha_defaults.get("region", "USA")),
        universe=str(alpha_defaults.get("universe", "TOP3000")),
        neutralization=str(alpha_defaults.get("neutralization", "SUBINDUSTRY")),
        auto_submit=bool(config.settings.get("pipeline", {}).get("auto_submit", False)),
        sim_throttle=int(config.settings.get("worldquant", {}).get("delay_seconds", 5)),
        max_daily_submissions=int(config.settings.get("worldquant", {}).get("daily_submit_limit", 1)),
        self_critique_rounds=int(config.settings.get("pipeline", {}).get("self_critique_rounds", 2)),
        enable_research=bool(config.settings.get("pipeline", {}).get("enable_research", True)),
        custom_research_prompt=str(config.settings.get("pipeline", {}).get("custom_research_prompt", "")),
    )


def merge_settings_payload(config: AppConfig, payload: dict[str, Any]) -> SettingsPayload:
    current = current_settings_payload(config).model_dump()
    current.update(payload)
    return SettingsPayload(**current)


def save_settings(config: AppConfig, payload: dict[str, Any]) -> str:
    merged = merge_settings_payload(config, payload)
    env_path = ROOT / ".env"
    env_lines = env_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    current_env = dict(config.env)
    replacements = {
        "WQ_USERNAME": merged.worldquant_username or current_env.get("WQ_USERNAME", ""),
        "WQ_PASSWORD": merged.worldquant_password or current_env.get("WQ_PASSWORD", ""),
        "OPENROUTER_API_KEY": merged.openrouter_api_key or current_env.get("OPENROUTER_API_KEY", ""),
    }
    updated_lines: list[str] = []
    seen: set[str] = set()
    for line in env_lines:
        if "=" not in line or line.strip().startswith("#"):
            updated_lines.append(line)
            continue
        key, _ = line.split("=", 1)
        key = key.strip()
        if key in replacements:
            updated_lines.append(f"{key}={replacements[key]}")
            seen.add(key)
        else:
            updated_lines.append(line)
    for key, value in replacements.items():
        if key not in seen:
            updated_lines.append(f"{key}={value}")
    env_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    settings_path = ROOT / "config" / "settings.yaml"
    alpha_path = ROOT / "config" / "alpha_config.yaml"
    settings_data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
    alpha_data = yaml.safe_load(alpha_path.read_text(encoding="utf-8")) or {}

    settings_data.setdefault("worldquant", {})
    settings_data["worldquant"]["delay_seconds"] = merged.sim_throttle
    settings_data["worldquant"]["daily_submit_limit"] = merged.max_daily_submissions
    settings_data.setdefault("pipeline", {})
    settings_data["pipeline"]["llm_batch"] = merged.alphas_per_run
    settings_data["pipeline"]["self_critique_rounds"] = merged.self_critique_rounds
    settings_data["pipeline"]["enable_research"] = merged.enable_research
    settings_data["pipeline"]["auto_submit"] = merged.auto_submit
    settings_data["pipeline"]["custom_research_prompt"] = merged.custom_research_prompt

    alpha_data.setdefault("defaults", {})
    alpha_data["defaults"]["region"] = merged.region
    alpha_data["defaults"]["universe"] = merged.universe
    alpha_data["defaults"]["neutralization"] = merged.neutralization

    settings_path.write_text(yaml.safe_dump(settings_data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    alpha_path.write_text(yaml.safe_dump(alpha_data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    reset_runtime_cache()
    return "Settings saved to .env, config/settings.yaml, and config/alpha_config.yaml."


def test_settings_connection(config: AppConfig, payload: SettingsTestRequest) -> dict[str, Any]:
    provider = payload.provider.strip().lower()
    if provider != "worldquant":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {payload.provider}")
    username = payload.worldquant_username or config.env.get("WQ_USERNAME", "")
    password = payload.worldquant_password or config.env.get("WQ_PASSWORD", "")
    if not username or not password:
        return {"status": "error", "provider": "worldquant", "message": "Missing WorldQuant credentials."}
    session = WQSessionManager(
        username=username,
        password=password,
        base_url=str(config.settings["worldquant"]["base_url"]),
        dry_run=config.dry_run,
    )
    try:
        session.login()
        mode = "dry-run" if config.dry_run else "live"
        return {"status": "ok", "provider": "worldquant", "message": f"WorldQuant connection test succeeded ({mode})."}
    except Exception as exc:
        return {"status": "error", "provider": "worldquant", "message": str(exc)}


def serialize_pipeline_run(run: dict[str, Any]) -> dict[str, Any]:
    item = dict(run)
    try:
        item["summary"] = json.loads(str(item.get("summary_json") or "{}"))
    except json.JSONDecodeError:
        item["summary"] = {}
    try:
        item["tags"] = json.loads(str(item.get("tags_json") or "{}"))
    except json.JSONDecodeError:
        item["tags"] = {}
    item["submit_enabled"] = bool(item.get("submit_enabled"))
    item["dry_run"] = bool(item.get("dry_run"))
    item.pop("summary_json", None)
    item.pop("tags_json", None)
    return item


def serialize_pipeline_event(event: dict[str, Any]) -> dict[str, Any]:
    item = dict(event)
    try:
        item["payload"] = json.loads(str(item.get("payload_json") or "{}"))
    except json.JSONDecodeError:
        item["payload"] = {}
    item.pop("payload_json", None)
    return item


def serialize_research_artifact(item: dict[str, Any]) -> dict[str, Any]:
    return dict(item)


def build_alpha_detail(alpha_id: int) -> dict[str, Any]:
    config = get_config()
    store = get_store()
    raw_row = store.get_alpha(alpha_id)
    if not raw_row:
        raise HTTPException(status_code=404, detail="Alpha not found.")
    row = parse_alpha_row(raw_row)
    theories = [normalize_theory_row(item) for item in store.list_theory_entries(limit=400)] or THEORY_CATALOG
    features = parse_expression_features(row["expression"])
    explanation = parse_explanation_row(store.get_alpha_explanation(alpha_id))
    if explanation is None:
        matched = match_theories(row["expression"], theories)
        reconstructed = build_alpha_explanation_payload(
            row["expression"],
            prompt_context=str(row.get("rationale") or ""),
            agent_reviews=row["agent_reviews_json"],
            stage_notes={"round_1": {"expression": row["expression"], "critique": "Loaded from stored run data."}},
        )
        explanation = {
            "theme": reconstructed["theme"],
            "hypothesis": reconstructed["hypothesis"],
            "prompt_context": reconstructed["prompt_context"],
            "expected_metrics_json": reconstructed["expected_metrics"],
            "risks_json": ["Reconstructed explanation because no persisted explanation exists yet.", *reconstructed["risks"]],
            "theory_ids_json": [item["id"] for item in matched] or reconstructed["theory_ids"],
            "research_refs_json": reconstructed["research_refs"],
            "field_info_json": reconstructed["field_info"],
            "operator_info_json": reconstructed["operator_info"],
            "agent_reviews_json": reconstructed["agent_reviews"],
            "stage_notes_json": reconstructed["stage_notes"],
        }
    theory_map = {item["id"]: item for item in theories}
    matched_theories = [theory_map[item] for item in explanation.get("theory_ids_json", []) if item in theory_map]
    run_id = row.get("run_id")
    research = [serialize_research_artifact(item) for item in store.list_research_artifacts(run_id=run_id, limit=24)] if run_id else []
    related_documents = find_relevant_documents(ROOT, row["expression"], limit=6)
    analysis = build_alpha_analysis(row, explanation, matched_theories or match_theories(row["expression"], theories), research, related_documents)
    return {
        "alpha": row,
        "features": features,
        "field_info": explanation.get("field_info_json") or explain_data_fields(features["fields"]),
        "operator_info": explanation.get("operator_info_json") or explain_operators(features["operators"]),
        "explanation": {
            "theme": explanation.get("theme", features["theme"]),
            "hypothesis": explanation.get("hypothesis", features["hypothesis"]),
            "prompt_context": explanation.get("prompt_context", ""),
            "expected_metrics": explanation.get("expected_metrics_json", {}),
            "risks": explanation.get("risks_json", []),
            "theory_ids": explanation.get("theory_ids_json", []),
            "research_refs": explanation.get("research_refs_json", []),
            "agent_reviews": explanation.get("agent_reviews_json", row["agent_reviews_json"]),
            "stage_notes": explanation.get("stage_notes_json", {}),
        },
        "analysis": analysis,
        "matched_theories": matched_theories or match_theories(row["expression"], theories),
        "checks": row["checks_json"],
        "research": research,
        "related_documents": related_documents,
    }


def create_app(root: Path | None = None) -> FastAPI:
    app_root = Path(root or ROOT).resolve()
    app = FastAPI(title="WQ Brain Alpha Monitor API", version="2.0.0")
    clear_site_data_headers = {
        "Clear-Site-Data": '"cache", "storage"',
        "Cache-Control": "no-store",
    }
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8506", "http://127.0.0.1:8506"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"status": "ok"}

    @app.get("/api/options")
    def options() -> dict[str, Any]:
        store = get_store()
        db_theories = store.list_theory_entries(status=None, limit=500)
        if db_theories:
            domains = sorted({item["domain"] for item in db_theories})
            sectors: list[str] = []
            for item in db_theories:
                try:
                    tags = json.loads(str(item.get("sector_tags_json") or "[]"))
                    sectors.extend(tags)
                except json.JSONDecodeError:
                    pass
            sectors = sorted(set(sectors))
        else:
            domains = sorted({item["domain"] for item in THEORY_CATALOG})
            sectors = sorted({tag for item in THEORY_CATALOG for tag in item["sector_tags"]})
        return {
            "strategy_options": STRATEGY_OPTIONS,
            "universe_options": UNIVERSE_OPTIONS,
            "neutralization_options": NEUTRALIZATION_OPTIONS,
            "theory_domains": domains,
            "theory_sectors": sectors,
        }

    @app.get("/api/overview")
    def overview() -> dict[str, Any]:
        config = get_config()
        store = get_store()
        rows = [parse_alpha_row(item) for item in store.list_recent(limit=200)]
        latest_run = store.latest_pipeline_run()
        latest_events = (
            [serialize_pipeline_event(item) for item in store.list_pipeline_events(run_id=str(latest_run.get("run_id")), limit=40)]
            if latest_run
            else []
        )
        primary_log = find_primary_log(app_root)
        log_lines = tail_file(primary_log, limit=160)
        alerts = compute_notifications(rows, config)
        if latest_run and str(latest_run.get("status") or "").lower() == "failed":
            failed_event = next((event for event in latest_events if event.get("event_type") == "run_failed"), None)
            alerts.insert(
                0,
                {
                    "kind": "error",
                    "title": "Latest run failed before simulation completed",
                    "body": str((failed_event or {}).get("message") or f"Run {latest_run.get('run_id')} failed."),
                },
            )
        elif latest_run and latest_run.get("summary_json"):
            try:
                summary = json.loads(str(latest_run.get("summary_json") or "{}"))
            except json.JSONDecodeError:
                summary = {}
            if int(summary.get("tested") or 0) == 0:
                alerts.insert(
                    0,
                    {
                        "kind": "warning",
                        "title": "Run finished without simulation output",
                        "body": "The workflow ended before any alpha was simulated. Check research credentials, rate limits, or upstream API errors.",
                    },
                )
        return {
            "summary": summarize_rows(rows),
            "latest_run": serialize_pipeline_run(latest_run) if latest_run else None,
            "progress": parse_progress(log_lines, latest_run, latest_events),
            "workflow_detail": build_workflow_detail(app_root, store, latest_run, latest_events),
            "feed": build_activity_feed_from_events(latest_events) if latest_events else [],
            "histogram": build_histogram(rows),
            "alerts": alerts,
            "best_alpha": build_alpha_table(sorted(rows, key=lambda row: float(row.get("fitness") or 0.0), reverse=True)[:1]),
            "latest_report": latest_report(config),
        }

    @app.get("/api/pipeline/runs")
    def pipeline_runs(limit: int = 20) -> dict[str, Any]:
        store = get_store()
        return {"items": [serialize_pipeline_run(item) for item in store.list_pipeline_runs(limit=limit)]}

    @app.get("/api/pipeline/runs/{run_id}/events")
    def pipeline_run_events(run_id: str, limit: int = 120) -> dict[str, Any]:
        store = get_store()
        return {"items": [serialize_pipeline_event(item) for item in store.list_pipeline_events(run_id=run_id, limit=limit)]}

    @app.get("/api/pipeline/runs/{run_id}/research")
    def pipeline_run_research(run_id: str, limit: int = 40) -> dict[str, Any]:
        store = get_store()
        return {"items": [serialize_research_artifact(item) for item in store.list_research_artifacts(run_id=run_id, limit=limit)]}

    @app.get("/api/alphas")
    def alphas(
        status: str | None = None,
        sharpe_min: float | None = None,
        theme: str | None = None,
        search: str | None = None,
        run_id: str | None = None,
        limit: int = 300,
    ) -> dict[str, Any]:
        store = get_store()
        rows = [parse_alpha_row(item) for item in store.list_recent(limit=limit, run_id=run_id)]
        table = build_alpha_table(rows)
        filtered: list[dict[str, Any]] = []
        for item in table:
            if status and item["status"].lower() != status.lower():
                continue
            if sharpe_min is not None and float(item["sharpe"]) < sharpe_min:
                continue
            if theme and item["theme"].lower() != theme.lower():
                continue
            if search and search.lower() not in item["expression"].lower():
                continue
            filtered.append(item)
        return {
            "items": filtered,
            "summary": summarize_rows(rows),
            "correlation_matrix": build_similarity_matrix(rows),
        }

    @app.get("/api/alphas/{alpha_id}")
    def alpha_detail(alpha_id: int) -> dict[str, Any]:
        return build_alpha_detail(alpha_id)

    @app.get("/api/research")
    def research(run_id: str | None = None, limit: int = 40) -> dict[str, Any]:
        config = get_config()
        store = get_store()
        chosen_run_id = run_id or (store.latest_pipeline_run() or {}).get("run_id")
        artifacts = (
            [serialize_research_artifact(item) for item in store.list_research_artifacts(run_id=chosen_run_id, limit=limit)]
            if chosen_run_id
            else []
        )
        alphas = [parse_alpha_row(item) for item in store.list_recent(limit=120, run_id=chosen_run_id)]
        mapping: list[dict[str, Any]] = []
        for artifact in artifacts:
            related = [
                {"id": item["id"], "expression": item["expression"], "status": item["status"], "sharpe": item["sharpe"]}
                for item in alphas
                if artifact.get("related_alpha_expression")
                and canonicalize(str(artifact["related_alpha_expression"])) == canonicalize(item["expression"])
            ]
            mapping.append(
                {
                    "artifact_id": artifact["id"],
                    "title": artifact["title"],
                    "query_text": artifact.get("query_text"),
                    "kind": artifact["kind"],
                    "content": artifact["content"],
                    "related_alphas": related,
                    "influence_score": min(100, 40 + len(related) * 20 + (10 if artifact.get("score") else 0)),
                }
            )
        return {
            "run_id": chosen_run_id,
            "artifacts": artifacts,
            "mapping": mapping,
            "recent_files": recent_research_files(),
            "latest_simulated_report": latest_simulated_report(app_root),
            "latest_report": latest_report(config),
        }

    @app.get("/api/analytics/failure-patterns")
    def failure_patterns(limit: int = 400) -> dict[str, Any]:
        return summarize_failure_patterns(get_store(), limit=limit)

    @app.get("/api/logs")
    def logs(path: str | None = None, limit: int = 160) -> dict[str, Any]:
        log_root = app_root / "logs"
        selected = find_primary_log(app_root)
        if path:
            candidate = Path(path).resolve()
            if not candidate.is_relative_to(log_root.resolve()):
                raise HTTPException(status_code=400, detail="Invalid log path.")
            selected = candidate
        store = get_store()
        latest_run = store.latest_pipeline_run()
        events = [serialize_pipeline_event(item) for item in store.list_pipeline_events(run_id=(latest_run or {}).get("run_id"), limit=150)] if latest_run else []
        return {
            "selected_path": str(selected) if selected else None,
            "available_files": [str(item) for item in latest_log_files(app_root)],
            "tail": tail_file(selected, limit=limit),
            "events": events,
        }

    @app.get("/api/settings")
    def settings() -> dict[str, Any]:
        config = get_config()
        current = current_settings_payload(config)
        return {
            "credentials": {
                "worldquant_username": config.env.get("WQ_USERNAME", ""),
                "worldquant_password_masked": mask_secret(config.env.get("WQ_PASSWORD", "")),
                "openrouter_api_key_masked": mask_secret(config.env.get("OPENROUTER_API_KEY", "")),
            },
            "pipeline": {
                "alphas_per_run": current.alphas_per_run,
                "region": current.region,
                "universe": current.universe,
                "neutralization": current.neutralization,
                "auto_submit": current.auto_submit,
                "sim_throttle": current.sim_throttle,
                "max_daily_submissions": current.max_daily_submissions,
            },
            "ai": {
                "self_critique_rounds": current.self_critique_rounds,
                "enable_research": current.enable_research,
                "custom_research_prompt": current.custom_research_prompt,
            },
        }

    @app.post("/api/settings")
    def update_settings(payload: SettingsPatchPayload) -> dict[str, Any]:
        message = save_settings(get_config(), payload.model_dump(exclude_none=True))
        return {"status": "ok", "message": message}

    @app.post("/api/settings/test")
    def settings_test(payload: SettingsTestRequest) -> dict[str, Any]:
        return test_settings_connection(get_config(), payload)

    @app.post("/api/actions/run")
    def start_run(payload: RunRequest) -> dict[str, Any]:
        return run_pipeline_now(payload)

    @app.post("/api/actions/stop")
    def stop_run() -> dict[str, Any]:
        return stop_pipeline_jobs()

    @app.get("/api/theories")
    def theories(
        domain: str | None = None,
        search: str | None = None,
        sector: str | None = None,
        limit: int = 240,
    ) -> dict[str, Any]:
        store = get_store()
        rows = [normalize_theory_row(item) for item in store.list_theory_entries(domain=domain, search=search, limit=limit)]
        if sector:
            rows = [item for item in rows if sector in item["sector_tags"]]
        return {"items": rows, "summary": domain_summary(rows)}

    @app.get("/api/theories/usage")
    def theory_usage(limit: int = 400) -> dict[str, Any]:
        return summarize_theory_usage(get_store(), limit=limit)

    @app.get("/api/events/stream")
    async def events_stream(run_id: str | None = None):
        import asyncio
        from fastapi.responses import StreamingResponse as _SR
        store_ref = get_store()
        async def _gen():
            last_id = 0
            try:
                while True:
                    events = store_ref.list_pipeline_events(run_id=run_id, limit=30)
                    new_events = [e for e in events if int(e.get("id") or 0) > last_id]
                    if new_events:
                        last_id = max(int(e.get("id") or 0) for e in new_events)
                        for event in reversed(new_events):
                            data = json.dumps(serialize_pipeline_event(event))
                            yield f"data: {data}\n\n"
                    else:
                        yield ": ping\n\n"
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                return
        return _SR(
            _gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/chat/messages")
    def get_chat_messages(session: str = "studio", limit: int = 60) -> dict[str, Any]:
        config = get_config()
        try:
            with db_connect(config) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session TEXT NOT NULL,
                        role TEXT NOT NULL,
                        agent TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                rows = conn.execute(
                    "SELECT * FROM chat_messages WHERE session=? ORDER BY id DESC LIMIT ?",
                    (session, limit),
                ).fetchall()
            items = list(reversed([dict(row) for row in rows]))
        except Exception:
            items = []
        return {"items": items}

    @app.post("/api/chat/messages")
    def post_chat_message(payload: dict[str, Any]) -> dict[str, Any]:
        config = get_config()
        session = str(payload.get("session") or "studio")
        role = str(payload.get("role") or "user")
        agent = str(payload.get("agent") or "user")
        content = str(payload.get("content") or "")
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            with db_connect(config) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session TEXT NOT NULL,
                        role TEXT NOT NULL,
                        agent TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                cursor = conn.execute(
                    "INSERT INTO chat_messages (session, role, agent, content, created_at) VALUES (?,?,?,?,?)",
                    (session, role, agent, content, created_at),
                )
                conn.commit()
                msg_id = cursor.lastrowid
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"id": msg_id, "session": session, "role": role, "agent": agent, "content": content, "created_at": created_at}

    @app.delete("/api/chat/messages")
    def clear_chat_messages(session: str = "studio") -> dict[str, Any]:
        config = get_config()
        try:
            with db_connect(config) as conn:
                conn.execute("DELETE FROM chat_messages WHERE session=?", (session,))
                conn.commit()
        except Exception:
            pass
        return {"status": "cleared", "session": session}

    @app.post("/api/theories")
    def upsert_theory(payload: TheoryPayload) -> dict[str, Any]:
        pipeline = get_pipeline()
        pipeline.add_or_update_theory(
            payload.theory_id,
            domain=payload.domain,
            title=payload.title,
            sector_tags=payload.sector_tags,
            core_principle=payload.core_principle,
            alpha_implication=payload.alpha_implication,
            example_expression=payload.example_expression,
            agent_reasoning=payload.agent_reasoning,
            source=payload.source,
            created_by=payload.created_by,
            status=payload.status,
        )
        reset_runtime_cache()
        return {"status": "ok", "theory_id": payload.theory_id}

    @app.post("/api/studio/context")
    def studio_context(payload: StudioContextRequest) -> dict[str, Any]:
        return load_context_bundle(get_pipeline(), payload.strategy_type, payload.focus_query)

    @app.post("/api/studio/query")
    def studio_query(payload: StudioQueryRequest) -> dict[str, Any]:
        responses = query_agents(get_pipeline(), payload.target, payload.prompt)
        validator = get_validator()
        extracted = {agent: extract_expressions(text, validator) for agent, text in responses.items()}
        return {"responses": responses, "extracted": extracted}

    @app.post("/api/studio/generate")
    def studio_generate(payload: StudioGenerateRequest) -> dict[str, Any]:
        prompt = build_generation_prompt(payload.strategy_type, payload.objective, payload.count, payload.context)
        responses = query_agents(get_pipeline(), payload.target, prompt)
        validator = get_validator()
        return {
            "prompt": prompt,
            "responses": responses,
            "extracted": {agent: extract_expressions(text, validator) for agent, text in responses.items()},
        }

    @app.post("/api/studio/simulate")
    def studio_simulate(payload: StudioSimulateRequest) -> dict[str, Any]:
        return simulate_candidate(
            get_pipeline(),
            get_validator(),
            payload.expression,
            payload.strategy_type,
            payload.metadata,
            payload.review_context,
        )

    frontend_dist = app_root / "frontend" / "dist"
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/_stcore/{path:path}", include_in_schema=False)
    async def redirect_stcore(path: str):
        del path
        return RedirectResponse(url="/", status_code=301)

    @app.get("/", include_in_schema=False)
    def root_index():
        if frontend_dist.exists():
            return FileResponse(frontend_dist / "index.html", headers=clear_site_data_headers)
        return JSONResponse({"status": "missing_frontend_build"})

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")
        if frontend_dist.exists():
            requested = (frontend_dist / full_path).resolve()
            if requested.exists() and requested.is_file() and requested.is_relative_to(frontend_dist.resolve()):
                return FileResponse(requested)
            return FileResponse(frontend_dist / "index.html", headers=clear_site_data_headers)
        return JSONResponse({"status": "missing_frontend_build", "path": full_path}, status_code=404)

    return app


app = create_app()
