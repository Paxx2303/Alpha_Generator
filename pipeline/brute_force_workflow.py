from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from config import AppConfig
from pipeline.alpha_pipeline import AlphaPipeline
from pipeline.models import AlphaCandidate, EvaluatedAlpha, SimulationMetrics
from pipeline.workflow_tracker import WorkflowTracker


import logging


LOGGER = logging.getLogger(__name__)


class BruteForceAlphaWorkflow:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.pipeline = AlphaPipeline(config)
        self.brute_config = config.alpha.get("brute_force", {})

    def run(
        self,
        strategy_type: str | None = None,
        count: int | None = None,
        skip: int = 0,
        submit_enabled: bool = False,
    ) -> dict[str, Any]:
        defaults = self.config.alpha_defaults
        strategy_type = strategy_type or defaults.get("strategy_type", "momentum")
        max_candidates = count or int(self.brute_config.get("max_candidates", 24))

        tracker = WorkflowTracker(
            self.pipeline.store,
            workflow_type="bruteforce",
            strategy_type=strategy_type,
            target_count=max_candidates,
            submit_enabled=submit_enabled,
            dry_run=self.config.dry_run,
            run_tags=self.pipeline._build_run_tags(
                strategy_type,
                max_candidates,
                submit_enabled,
                workflow_type="bruteforce",
                extra={"skip": skip, "candidate_family_mode": "grid_search"},
            ),
        )
        try:
            tracker.set_stage("research", "Refreshing research context for brute-force sweep.")
            research_digest = self.pipeline.daily_researcher.refresh()
            self.pipeline.knowledge_base.load_all()
            research_summary = self.pipeline._research_market(strategy_type)
            context = self.pipeline._build_context(strategy_type, research_summary, research_digest)
            metric_research_context = self.pipeline.knowledge_base.query_context(
                "WorldQuant Brain sharpe fitness turnover drawdown self correlation decay truncation neutralization"
            )
            digest_ref = tracker.research_artifact("daily_digest", "Daily research digest", research_digest[:12000], query_text=strategy_type)
            summary_ref = tracker.research_artifact("market_summary", "Market research summary", research_summary[:12000], query_text=strategy_type)
            metric_ref = tracker.research_artifact("metric_context", "Metric interpretation context", metric_research_context[:12000], query_text="metrics")

            tracker.set_stage("generate", "Building brute-force candidate grid.")
            build_count = max_candidates + max(skip, 0)
            candidates = self._build_candidates(strategy_type, build_count)
            if skip > 0:
                candidates = candidates[skip : skip + max_candidates]
            tracker.event("generate", "INFO", "candidate_grid", f"Prepared {len(candidates)} brute-force candidates.", payload={"skip": skip})

            tracker.set_stage("pre_backtest", "Running local proxy backtests before brute-force live simulation.")
            candidates, screened_out = self.pipeline._rank_candidates_for_live_simulation(
                candidates,
                strategy_type=strategy_type,
                base_context=context,
                tracker=tracker,
                research_refs=[
                    {"artifact_id": digest_ref, "kind": "daily_digest"},
                    {"artifact_id": summary_ref, "kind": "market_summary"},
                    {"artifact_id": metric_ref, "kind": "metric_context"},
                ],
                target_count=max_candidates,
            )

            tracker.set_stage("simulate", "Running brute-force simulation and gating.")
            evaluated = self._evaluate_candidates(
                candidates,
                submit_enabled=submit_enabled,
                tracker=tracker,
                prompt_context=context,
                research_refs=[
                    {"artifact_id": digest_ref, "kind": "daily_digest"},
                    {"artifact_id": summary_ref, "kind": "market_summary"},
                    {"artifact_id": metric_ref, "kind": "metric_context"},
                ],
            )

            tracker.set_stage("filter", "Analyzing winners and losers by family.")
            family_summary = self._summarize_by_family(evaluated)
            top_candidates = self._top_candidates(evaluated, limit=8)
            bottom_candidates = self._bottom_candidates(evaluated, limit=8)
            metric_leaders = self._best_metric_candidates(evaluated)
            analysis = self._agent_pattern_analysis(
                strategy_type=strategy_type,
                family_summary=family_summary,
                top_candidates=top_candidates,
                bottom_candidates=bottom_candidates,
                metric_leaders=metric_leaders,
                context=context,
                metric_research_context=metric_research_context,
            )
            tracker.research_artifact("agent_analysis", "Brute-force pattern analysis", json_like(analysis), query_text=strategy_type)

            tracker.set_stage("store", "Writing brute-force learning note and run summary.")
            note_path = self._write_learning_note(
                strategy_type=strategy_type,
                family_summary=family_summary,
                top_candidates=top_candidates,
                bottom_candidates=bottom_candidates,
                metric_leaders=metric_leaders,
                analysis=analysis,
            )
            self.pipeline.knowledge_base.load_all()

            report = {
                "run_id": tracker.run_id,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "strategy_type": strategy_type,
                "dry_run": self.config.dry_run,
                "skip_count": skip,
                "candidate_count": len(candidates),
                "evaluated_count": len(evaluated),
                "submitted_count": sum(1 for item in evaluated if item.status == "submitted"),
                "pre_backtest_promoted": len(candidates),
                "pre_backtest_screened_out": screened_out,
                "family_summary": family_summary,
                "top_candidates": top_candidates,
                "bottom_candidates": bottom_candidates,
                "metric_leaders": metric_leaders,
                "analysis": analysis,
                "learning_note": str(note_path),
            }
            self.pipeline.store.save_daily_report(datetime.now().strftime("%Y-%m-%d"), report, run_id=tracker.run_id)
            tracker.complete(report)
            return report
        except Exception as exc:
            tracker.fail(str(exc), payload={"strategy_type": strategy_type, "skip": skip})
            raise

    def _build_candidates(self, strategy_type: str, max_candidates: int) -> list[AlphaCandidate]:
        families: dict[str, list[str]] = (
            self.brute_config.get("template_families", {}).get(strategy_type, {})
        )
        lookbacks: list[int] = self.brute_config.get("lookbacks", [5, 10, 20, 60])
        decay_values: list[int] = self.brute_config.get("decay_values", [6])
        truncation_values: list[float] = self.brute_config.get("truncation_values", [0.08])
        neutralizations: list[str] = self.brute_config.get("neutralizations", ["SUBINDUSTRY"])
        delays: list[int] = self.brute_config.get("delays", [1])
        candidates: list[AlphaCandidate] = []
        buckets: list[list[AlphaCandidate]] = []
        for family_name, templates in families.items():
            for template in templates:
                bucket: list[AlphaCandidate] = []
                for lookback in lookbacks:
                    for decay in decay_values:
                        for truncation in truncation_values:
                            for neutralization in neutralizations:
                                for delay in delays:
                                    expression = template.format(lookback=lookback)
                                    bucket.append(
                                        AlphaCandidate(
                                            expression=expression,
                                            source="bruteforce",
                                            strategy_type=strategy_type,
                                            rationale=(
                                                f"Brute-force sweep for family={family_name}, lookback={lookback}, "
                                                f"decay={decay}, truncation={truncation}, "
                                                f"neutralization={neutralization}, delay={delay}."
                                            ),
                                            metadata={
                                                "generation_source": "bruteforce_grid",
                                                "origin_agent": "bruteforce_grid",
                                                "family": family_name,
                                                "lookback": lookback,
                                                "delay": delay,
                                                "universe": "TOP3000",
                                                "truncation": truncation,
                                                "region": "USA",
                                                "decay": decay,
                                                "neutralization": neutralization,
                                                "pasteurization": "ON",
                                                "nanHandling": "OFF",
                                            },
                                        )
                                    )
                if bucket:
                    buckets.append(bucket)

        while len(candidates) < max_candidates and buckets:
            next_buckets: list[list[AlphaCandidate]] = []
            for bucket in buckets:
                if bucket:
                    candidates.append(bucket.pop(0))
                    if len(candidates) >= max_candidates:
                        break
                if bucket:
                    next_buckets.append(bucket)
            buckets = next_buckets
        return candidates

    def _evaluate_candidates(
        self,
        candidates: list[AlphaCandidate],
        submit_enabled: bool,
        tracker: WorkflowTracker | None = None,
        prompt_context: str = "",
        research_refs: list[dict[str, Any]] | None = None,
    ) -> list[EvaluatedAlpha]:
        evaluated: list[EvaluatedAlpha] = []
        history = self.pipeline.store.list_recent(limit=200)

        total = len(candidates)
        for index, candidate in enumerate(candidates, start=1):
            if index == 1 or index % 10 == 0 or index == total:
                LOGGER.info(
                    "Brute-force progress %s/%s | family=%s | expression=%s",
                    index,
                    total,
                    candidate.metadata.get("family", "unknown"),
                    candidate.expression,
                )
            if tracker is not None:
                tracker.event(
                    "simulate",
                    "INFO",
                    "candidate_started",
                    f"Brute-force candidate {index}/{total}.",
                    alpha_expression=candidate.expression,
                    payload={"metadata": candidate.metadata},
                )
            errors = self.pipeline.validator.validate(candidate.expression)
            if errors:
                metrics = SimulationMetrics(
                    sharpe=0.0,
                    fitness=0.0,
                    annual_returns=0.0,
                    turnover=0.0,
                    drawdown=1.0,
                    self_correlation=1.0,
                    notes="Validation failed during brute-force workflow.",
                )
                item = EvaluatedAlpha(
                    candidate=candidate,
                    metrics=metrics,
                    validation_errors=errors,
                    gate_passed=False,
                    gate_reasons=errors,
                    status="invalid",
                )
                alpha_run_id = self.pipeline.store.insert_alpha(
                    candidate,
                    metrics,
                    item.status,
                    notes="; ".join(errors),
                    run_id=tracker.run_id if tracker else None,
                    generation_source=self.pipeline._generation_source(candidate),
                    origin_agent=self.pipeline._origin_agent(candidate),
                    run_tags=self.pipeline._candidate_run_tags(candidate, tracker.run_id if tracker else None),
                    gate_failure_reason=errors[0] if errors else None,
                )
                if tracker is not None:
                    tracker.alpha_explanation(
                        alpha_run_id,
                        candidate,
                        thresholds=self.pipeline.quality_gate.thresholds,
                        prompt_context=prompt_context,
                        research_refs=research_refs,
                        stage_notes={"validation_errors": errors},
                    )
                    tracker.event(
                        "simulate",
                        "ERROR",
                        "candidate_invalid",
                        "Brute-force candidate failed validation.",
                        alpha_expression=candidate.expression,
                        alpha_run_id=alpha_run_id,
                        payload={"errors": errors},
                    )
                evaluated.append(item)
                continue

            pre_backtest = self.pipeline.local_backtester.evaluate(candidate, history)
            if not pre_backtest.passed:
                self.pipeline._persist_screened_candidate(
                    candidate,
                    pre_backtest,
                    tracker=tracker,
                    base_context=prompt_context,
                    research_refs=research_refs,
                )
                evaluated.append(
                    EvaluatedAlpha(
                        candidate=candidate,
                        metrics=self.pipeline._pre_backtest_metrics(pre_backtest),
                        gate_passed=False,
                        gate_reasons=list(pre_backtest.reasons),
                        status="screened_out",
                    )
                )
                continue

            try:
                metrics = self.pipeline.simulator.run(candidate)
            except Exception as exc:
                metrics = SimulationMetrics(
                    sharpe=0.0,
                    fitness=0.0,
                    annual_returns=0.0,
                    turnover=0.0,
                    drawdown=1.0,
                    self_correlation=1.0,
                    notes=str(exc),
                )
                item = EvaluatedAlpha(
                    candidate=candidate,
                    metrics=metrics,
                    gate_passed=False,
                    gate_reasons=[f"Simulation failed: {exc}"],
                    status="tested",
                )
                alpha_run_id = self.pipeline.store.insert_alpha(
                    candidate,
                    metrics,
                    item.status,
                    notes="; ".join(item.gate_reasons),
                    run_id=tracker.run_id if tracker else None,
                    generation_source=self.pipeline._generation_source(candidate),
                    origin_agent=self.pipeline._origin_agent(candidate),
                    run_tags=self.pipeline._candidate_run_tags(candidate, tracker.run_id if tracker else None),
                    gate_failure_reason=item.gate_reasons[0] if item.gate_reasons else None,
                    pre_backtest_score=float(pre_backtest.score),
                    pre_backtest_passed=bool(pre_backtest.passed),
                    pre_backtest_metrics=self.pipeline.local_backtester.as_payload(pre_backtest).get("estimated_metrics", {}),
                )
                if tracker is not None:
                    tracker.alpha_explanation(
                        alpha_run_id,
                        candidate,
                        thresholds=self.pipeline.quality_gate.thresholds,
                        prompt_context=prompt_context,
                        research_refs=research_refs,
                        stage_notes={"simulation_error": item.gate_reasons, "pre_backtest": self.pipeline.local_backtester.as_payload(pre_backtest)},
                    )
                    tracker.event(
                        "simulate",
                        "ERROR",
                        "candidate_failed",
                        "Brute-force simulation failed.",
                        alpha_expression=candidate.expression,
                        alpha_run_id=alpha_run_id,
                        payload={"reasons": item.gate_reasons},
                    )
                evaluated.append(item)
                continue

            metrics.self_correlation = max(
                metrics.self_correlation,
                self.pipeline.correlation_checker.estimate_self_correlation(candidate, history),
            )
            gate_assessment = self.pipeline.quality_gate.assess(metrics)
            gate_failures = gate_assessment["failures"]
            gate_warnings = gate_assessment["warnings"]
            gate_reasons = [str(item["message"]) for item in gate_failures]
            gate_passed = not gate_reasons
            needs_review = gate_passed and bool(gate_warnings)
            status = "approved" if gate_passed else "tested"
            submitted_at: str | None = None

            if gate_passed and submit_enabled:
                if tracker is not None:
                    tracker.event("submit", "INFO", "submit_attempt", "Submitting brute-force winner.", alpha_expression=candidate.expression)
                submitted, result = self.pipeline.auto_submitter.submit(candidate)
                if submitted:
                    status = "submitted"
                    gate_reasons.append(f"Submission status: {result['status']}")
                    submitted_at = str(result.get("submitted_at") or "")
                else:
                    gate_reasons.append(result["reason"])
                    submitted_at = str(result.get("submitted_at") or "") or None

            item = EvaluatedAlpha(
                candidate=candidate,
                metrics=metrics,
                gate_passed=gate_passed,
                gate_reasons=gate_reasons,
                status=status,
            )
            alpha_run_id = self.pipeline.store.insert_alpha(
                candidate,
                metrics,
                status,
                notes="; ".join(gate_reasons),
                run_id=tracker.run_id if tracker else None,
                generation_source=self.pipeline._generation_source(candidate),
                origin_agent=self.pipeline._origin_agent(candidate),
                run_tags=self.pipeline._candidate_run_tags(candidate, tracker.run_id if tracker else None),
                gate_failure_reason=gate_reasons[0] if gate_reasons else None,
                needs_review=needs_review,
                submitted_at=submitted_at,
                pre_backtest_score=float(pre_backtest.score),
                pre_backtest_passed=bool(pre_backtest.passed),
                pre_backtest_metrics=self.pipeline.local_backtester.as_payload(pre_backtest).get("estimated_metrics", {}),
            )
            if tracker is not None:
                tracker.alpha_explanation(
                    alpha_run_id,
                    candidate,
                    thresholds=self.pipeline.quality_gate.thresholds,
                    prompt_context=prompt_context,
                    research_refs=research_refs,
                    stage_notes={
                        "pre_backtest": self.pipeline.local_backtester.as_payload(pre_backtest),
                        "gate_reasons": gate_reasons,
                        "gate_failures": gate_failures,
                        "gate_warnings": gate_warnings,
                        "needs_review": needs_review,
                        "metrics": asdict(metrics),
                        "status": status,
                    },
                )
                for failure in gate_failures:
                    tracker.event(
                        "filter",
                        "WARNING",
                        "GATE_FAIL",
                        str(failure["message"]),
                        alpha_expression=candidate.expression,
                        alpha_run_id=alpha_run_id,
                        payload=failure,
                    )
                for warning in gate_warnings:
                    tracker.event(
                        "filter",
                        "WARNING",
                        "GATE_WARNING",
                        str(warning["message"]),
                        alpha_expression=candidate.expression,
                        alpha_run_id=alpha_run_id,
                        payload={**warning, "needs_review": True},
                    )
                tracker.event(
                    "filter" if not gate_passed else "store",
                    "INFO" if gate_passed else "WARNING",
                    "candidate_result",
                    f"Brute-force candidate finished with status={status}.",
                    alpha_expression=candidate.expression,
                    alpha_run_id=alpha_run_id,
                    payload={"gate_reasons": gate_reasons, "gate_warnings": gate_warnings, "needs_review": needs_review, "metrics": asdict(metrics)},
                )
            evaluated.append(item)
            history.append({"expression": candidate.expression})

        return evaluated

    def _summarize_by_family(self, evaluated: list[EvaluatedAlpha]) -> list[dict[str, Any]]:
        grouped: dict[str, list[EvaluatedAlpha]] = defaultdict(list)
        for item in evaluated:
            family = str(item.candidate.metadata.get("family", "unknown"))
            grouped[family].append(item)

        summary: list[dict[str, Any]] = []
        for family, items in grouped.items():
            best_item = max(
                items,
                key=lambda item: (item.metrics.sharpe, item.metrics.fitness, item.metrics.annual_returns),
            )
            summary.append(
                {
                    "family": family,
                    "count": len(items),
                    "approved": sum(1 for item in items if item.status in {"approved", "submitted"}),
                    "avg_sharpe": round(mean(item.metrics.sharpe for item in items), 3),
                    "avg_fitness": round(mean(item.metrics.fitness for item in items), 3),
                    "avg_turnover": round(mean(item.metrics.turnover for item in items), 3),
                    "best_expression": best_item.candidate.expression,
                    "best_settings": best_item.candidate.metadata,
                }
            )
        return sorted(summary, key=lambda item: (item["approved"], item["avg_sharpe"], item["avg_fitness"]), reverse=True)

    @staticmethod
    def _top_candidates(evaluated: list[EvaluatedAlpha], limit: int = 5) -> list[dict[str, Any]]:
        ranked = sorted(
            evaluated,
            key=lambda item: (item.metrics.sharpe, item.metrics.fitness, item.metrics.annual_returns),
            reverse=True,
        )
        return [serialize_candidate(item) for item in ranked[:limit]]

    @staticmethod
    def _bottom_candidates(evaluated: list[EvaluatedAlpha], limit: int = 5) -> list[dict[str, Any]]:
        ranked = sorted(
            evaluated,
            key=lambda item: (item.metrics.sharpe, item.metrics.fitness, item.metrics.annual_returns),
        )
        return [serialize_candidate(item) for item in ranked[:limit]]

    @staticmethod
    def _best_metric_candidates(evaluated: list[EvaluatedAlpha]) -> dict[str, dict[str, Any]]:
        if not evaluated:
            return {}
        return {
            "best_sharpe": serialize_candidate(max(evaluated, key=lambda item: item.metrics.sharpe)),
            "best_fitness": serialize_candidate(max(evaluated, key=lambda item: item.metrics.fitness)),
            "best_returns": serialize_candidate(max(evaluated, key=lambda item: item.metrics.annual_returns)),
            "lowest_drawdown": serialize_candidate(min(evaluated, key=lambda item: item.metrics.drawdown)),
        }

    def _agent_pattern_analysis(
        self,
        strategy_type: str,
        family_summary: list[dict[str, Any]],
        top_candidates: list[dict[str, Any]],
        bottom_candidates: list[dict[str, Any]],
        metric_leaders: dict[str, dict[str, Any]],
        context: str,
        metric_research_context: str,
    ) -> dict[str, str]:
        metric_guide = (
            "Metric guide: higher Sharpe means better risk-adjusted return; "
            "higher Fitness means better return-turnover efficiency; "
            "higher returns are good if drawdown stays controlled; "
            "turnover too high can hurt robustness; lower drawdown and lower self-correlation are preferable."
        )
        prompt = (
            f"Analyze brute-force WorldQuant alpha results for strategy={strategy_type}.\n"
            f"Family summary: {family_summary}\n"
            f"Top candidates: {top_candidates}\n"
            f"Bottom candidates: {bottom_candidates}\n"
            f"Metric leaders: {metric_leaders}\n"
            f"{metric_guide}\n\n"
            "Explain:\n"
            "1. Which expression families are strongest.\n"
            "2. What structural pattern makes the winners good.\n"
            "3. Why the losers fail.\n"
            "4. What the simulation metrics imply about the alpha behavior.\n"
            "5. What brute-force expansions to test next.\n\n"
            f"Additional context:\n{context[:3000]}\n\n"
            f"Metric research context:\n{metric_research_context[:2500]}"
        )
        return {
            "hermes": self.pipeline.hermes.ask(prompt).strip(),
            "deerflow": self.pipeline.deerflow.run_research(prompt).strip(),
        }

    def _write_learning_note(
        self,
        strategy_type: str,
        family_summary: list[dict[str, Any]],
        top_candidates: list[dict[str, Any]],
        bottom_candidates: list[dict[str, Any]],
        metric_leaders: dict[str, dict[str, Any]],
        analysis: dict[str, str],
    ) -> Path:
        out_root = self.config.knowledge_root / "lessons_learned" / "bruteforce"
        out_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_root / f"{stamp}_{strategy_type}.md"
        lines = [
            f"# Brute Force Learning Note - {strategy_type}",
            "",
            "## Family Summary",
            "",
            json_like(family_summary),
            "",
            "## Top Candidates",
            "",
            json_like(top_candidates),
            "",
            "## Bottom Candidates",
            "",
            json_like(bottom_candidates),
            "",
            "## Metric Leaders",
            "",
            json_like(metric_leaders),
            "",
            "## Hermes Analysis",
            "",
            analysis.get("hermes", ""),
            "",
            "## DeerFlow Analysis",
            "",
            analysis.get("deerflow", ""),
            "",
        ]
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path


def json_like(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, indent=2)


def serialize_candidate(item: EvaluatedAlpha) -> dict[str, Any]:
    return {
        "expression": item.candidate.expression,
        "family": item.candidate.metadata.get("family", "unknown"),
        "settings": item.candidate.metadata,
        "sharpe": item.metrics.sharpe,
        "fitness": item.metrics.fitness,
        "returns": item.metrics.annual_returns,
        "turnover": item.metrics.turnover,
        "drawdown": item.metrics.drawdown,
        "self_correlation": item.metrics.self_correlation,
        "status": item.status,
    }
