from __future__ import annotations

import json
import time
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config
from pipeline.alpha_pipeline import AlphaPipeline
from pipeline.generator.expression_validator import ExpressionValidator
from pipeline.models import AlphaCandidate, SimulationMetrics


PACK_PATH = Path(
    r"C:\Using\Alpha_Generator\knowledge_base\generated_alpha_only\20260518_072155_hermes_deerflow_alpha_only.md"
)
OUT_ROOT = Path(r"C:\Using\Alpha_Generator\knowledge_base\generated_alpha_only\simulated")
CANONICAL_SPACES = re.compile(r"\s+")
SIMULATION_RETRIES = 3
RETRY_SLEEP_SECONDS = 8


def canonicalize(expression: str) -> str:
    return CANONICAL_SPACES.sub("", expression)


def parse_pack(path: Path) -> list[str]:
    expressions: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("- rank("):
            continue
        expression = line[2:].strip()
        key = canonicalize(expression)
        if key in seen:
            continue
        seen.add(key)
        expressions.append(expression)
    return expressions


def usable_cache(row: dict[str, Any]) -> bool:
    notes = str(row.get("notes") or "")
    if "Simulation failed" in notes:
        return False
    sharpe = float(row.get("sharpe") or 0.0)
    fitness = float(row.get("fitness") or 0.0)
    annual_returns = float(row.get("annual_returns") or 0.0)
    turnover = float(row.get("turnover") or 0.0)
    drawdown = float(row.get("drawdown") or 0.0)
    self_correlation = float(row.get("self_correlation") or 0.0)
    if (
        sharpe == 0.0
        and fitness == 0.0
        and annual_returns == 0.0
        and turnover == 0.0
        and drawdown >= 1.0
        and self_correlation >= 1.0
    ):
        return False
    return True


def simulate_with_retry(pipeline: AlphaPipeline, candidate: AlphaCandidate) -> SimulationMetrics:
    last_error: Exception | None = None
    for attempt in range(1, SIMULATION_RETRIES + 1):
        try:
            return pipeline.simulator.run(candidate)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(
                f"Simulation retry {attempt}/{SIMULATION_RETRIES} failed for {candidate.expression}: {exc}",
                flush=True,
            )
            if attempt < SIMULATION_RETRIES:
                time.sleep(RETRY_SLEEP_SECONDS)
    raise RuntimeError(str(last_error) if last_error else "Unknown simulation failure.")


def row_to_metrics(row: dict[str, Any]) -> SimulationMetrics:
    return SimulationMetrics(
        sharpe=float(row.get("sharpe") or 0.0),
        fitness=float(row.get("fitness") or 0.0),
        annual_returns=float(row.get("annual_returns") or 0.0),
        turnover=float(row.get("turnover") or 0.0),
        drawdown=float(row.get("drawdown") or 0.0),
        self_correlation=float(row.get("self_correlation") or 0.0),
        notes=str(row.get("notes") or ""),
        checks=[],
    )


def top_slice(items: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    ranked = sorted(
        items,
        key=lambda item: (
            item["metrics"]["sharpe"],
            item["metrics"]["fitness"],
            item["metrics"]["annual_returns"],
        ),
        reverse=True,
    )
    return ranked[:limit]


def bottom_slice(items: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    ranked = sorted(
        items,
        key=lambda item: (
            item["metrics"]["sharpe"],
            item["metrics"]["fitness"],
            item["metrics"]["annual_returns"],
        ),
    )
    return ranked[:limit]


def build_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "expression": item["expression"],
        "cache_used": item["cache_used"],
        "status": item["status"],
        "metrics": item["metrics"],
        "gate_reasons": item["gate_reasons"],
    }


def main() -> None:
    config = load_config()
    pipeline = AlphaPipeline(config)
    validator = ExpressionValidator()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    expressions = parse_pack(PACK_PATH)
    history = pipeline.store.list_recent(limit=1000)
    cache: dict[str, dict[str, Any]] = {}
    completed_eval_cache: dict[str, dict[str, Any]] = {}
    for row in history:
        key = canonicalize(str(row.get("expression") or ""))
        if not key:
            continue
        if row.get("source") == "generated_alpha_eval" and key not in completed_eval_cache:
            completed_eval_cache[key] = row
        existing = cache.get(key)
        if existing is None:
            cache[key] = row
            continue
        existing_usable = usable_cache(existing)
        current_usable = usable_cache(row)
        if current_usable and not existing_usable:
            cache[key] = row

    research_digest = pipeline.daily_researcher.refresh()
    pipeline.knowledge_base.load_all()
    context = pipeline._build_context(
        "momentum",
        pipeline._research_market("momentum"),
        research_digest,
    )
    reading_pack = pipeline.knowledge_base.query_context(
        "regime aware momentum liquidity turnover self correlation family diagnostics",
        k=4,
    )

    results: list[dict[str, Any]] = []
    live_count = 0
    cache_count = 0

    for expression in expressions:
        candidate = AlphaCandidate(
            expression=expression,
            source="generated_alpha_eval",
            strategy_type="momentum",
            rationale="Evaluation of alpha-only generation pack.",
            metadata={
                "delay": 1,
                "universe": "TOP3000",
                "truncation": 0.08,
                "region": "USA",
                "decay": 6,
                "neutralization": "SUBINDUSTRY",
                "pasteurization": "ON",
                "nanHandling": "OFF",
            },
        )
        key = canonicalize(expression)
        row = cache.get(key)
        completed_eval_row = completed_eval_cache.get(key)
        errors = validator.validate(expression)
        if errors:
            metrics = SimulationMetrics(
                sharpe=0.0,
                fitness=0.0,
                annual_returns=0.0,
                turnover=0.0,
                drawdown=1.0,
                self_correlation=1.0,
                notes="Validation failed before simulation.",
            )
            gate_reasons = errors
            status = "invalid"
            cache_used = False
        elif completed_eval_row and usable_cache(completed_eval_row):
            metrics = row_to_metrics(completed_eval_row)
            gate_reasons = pipeline.quality_gate.evaluate(metrics)
            status = str(completed_eval_row.get("status") or ("approved" if not gate_reasons else "tested"))
            cache_used = True
            cache_count += 1
        elif row and usable_cache(row):
            metrics = row_to_metrics(row)
            gate_reasons = pipeline.quality_gate.evaluate(metrics)
            status = "approved" if not gate_reasons else "tested"
            cache_used = True
            cache_count += 1
        else:
            try:
                metrics = simulate_with_retry(pipeline, candidate)
                metrics.self_correlation = max(
                    metrics.self_correlation,
                    pipeline.correlation_checker.estimate_self_correlation(candidate, history),
                )
                wq_failures = [
                    f"WQ check failed: {check.get('name')}."
                    for check in metrics.checks
                    if str(check.get("result")) == "FAIL"
                ]
                gate_reasons = wq_failures + pipeline.quality_gate.evaluate(metrics)
                status = "approved" if not gate_reasons else "tested"
            except Exception as exc:  # noqa: BLE001
                metrics = SimulationMetrics(
                    sharpe=0.0,
                    fitness=0.0,
                    annual_returns=0.0,
                    turnover=0.0,
                    drawdown=1.0,
                    self_correlation=1.0,
                    notes=str(exc),
                )
                gate_reasons = [f"Simulation failed: {exc}"]
                status = "tested"
            cache_used = False
            live_count += 1
            pipeline.store.insert_alpha(candidate, metrics, status, notes="; ".join(gate_reasons))
            history.append({"expression": expression})
            cache[key] = {
                "expression": expression,
                "status": status,
                "sharpe": metrics.sharpe,
                "fitness": metrics.fitness,
                "annual_returns": metrics.annual_returns,
                "turnover": metrics.turnover,
                "drawdown": metrics.drawdown,
                "self_correlation": metrics.self_correlation,
                "notes": "; ".join(gate_reasons),
                "source": "generated_alpha_eval",
            }

        results.append(
            {
                "expression": expression,
                "cache_used": cache_used,
                "status": status,
                "gate_reasons": gate_reasons,
                "metrics": {
                    "sharpe": metrics.sharpe,
                    "fitness": metrics.fitness,
                    "annual_returns": metrics.annual_returns,
                    "turnover": metrics.turnover,
                    "drawdown": metrics.drawdown,
                    "self_correlation": metrics.self_correlation,
                    "notes": metrics.notes,
                },
            }
        )

    top_candidates = [build_summary(item) for item in top_slice(results)]
    bottom_candidates = [build_summary(item) for item in bottom_slice(results)]
    approved = [item for item in results if item["status"] == "approved"]

    analysis_prompt = (
        "Analyze a WorldQuant alpha-only evaluation pack.\n"
        f"Top candidates: {json.dumps(top_candidates, ensure_ascii=False)}\n"
        f"Bottom candidates: {json.dumps(bottom_candidates, ensure_ascii=False)}\n"
        "Explain which formulas are strongest, why they work, why weak formulas fail, "
        "and what to generate next.\n\n"
        f"Reading pack:\n{reading_pack[:2500]}\n\n"
        f"Research context:\n{context[:2500]}"
    )
    hermes_analysis = pipeline.hermes.ask(analysis_prompt).strip()
    deerflow_analysis = pipeline.deerflow.run_research(analysis_prompt).strip()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUT_ROOT / f"{stamp}_alpha_only_simulated.md"
    lines = [
        f"# Alpha Only Simulated Evaluation - {stamp}",
        "",
        f"- Pack: {PACK_PATH}",
        f"- Total unique expressions: {len(expressions)}",
        f"- Cache reused: {cache_count}",
        f"- Live simulations run: {live_count}",
        f"- Approved: {len(approved)}",
        "",
        "## Top Candidates",
        "",
        "```json",
        json.dumps(top_candidates, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Bottom Candidates",
        "",
        "```json",
        json.dumps(bottom_candidates, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Full Results",
        "",
        "```json",
        json.dumps(results, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Hermes Analysis",
        "",
        hermes_analysis,
        "",
        "## DeerFlow Analysis",
        "",
        deerflow_analysis,
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "output_path": str(out_path),
                "total": len(expressions),
                "cache_reused": cache_count,
                "live_simulations": live_count,
                "approved": len(approved),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
