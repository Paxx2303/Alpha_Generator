from __future__ import annotations

from collections import deque
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import json
import logging
import re
from typing import Any

from api_layer import RateLimiter, WQSessionManager, WorldQuantClient
from config import AppConfig
from database import AlphaStore
from dashboard.theory_catalog import THEORY_CATALOG
from knowledge_base import WQKnowledgeBase
from knowledge_base.theory_accuracy_evaluator import TheoryAccuracyEvaluator
from orchestration.openai_fallback import OpenAIFallbackClient
from orchestration import DeerFlowBridge, HermesBridge, TaskRouter
from pipeline.analyzer import AlphaAnalyzer, CorrelationChecker, LocalBacktester, PatternFinder
from pipeline.generator import ExpressionValidator, GeneticEngine, LLMGenerator
from pipeline.models import (
    AgentReview,
    AlphaCandidate,
    EvaluatedAlpha,
    SimulationMetrics,
    aggregate_stage_verdict,
    average_stage_confidence,
)
from pipeline.research import DailyResearcher
from pipeline.scraper import PaperScraper, WQScraper
from pipeline.submission import AutoSubmitter, QualityGate, Simulator
from pipeline.workflow_tracker import WorkflowTracker


LOGGER = logging.getLogger(__name__)


class AlphaPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = AlphaStore(config.alpha_store_path)
        self.performance_store = AlphaStore(config.performance_log_path)

        session_manager = WQSessionManager(
            username=config.env.get("WQ_USERNAME", ""),
            password=config.env.get("WQ_PASSWORD", ""),
            base_url=config.settings["worldquant"]["base_url"],
            dry_run=config.dry_run,
        )
        rate_limiter = RateLimiter(config.settings["worldquant"]["delay_seconds"])
        self.client = WorldQuantClient(
            session_manager=session_manager,
            rate_limiter=rate_limiter,
            base_url=config.settings["worldquant"]["base_url"],
            dry_run=config.dry_run,
            queue_dir=config.root / "runtime" / "simulation_fifo",
        )

        hermes_cfg = config.settings["integrations"]["hermes"]
        deer_cfg = config.settings["integrations"]["deerflow"]
        fallback_cfg = config.settings["integrations"].get("openrouter_fallback", {})
        fallback_client = OpenAIFallbackClient(
            api_key=config.env.get("OPENROUTER_API_KEY", ""),
            base_url=fallback_cfg.get("base_url", "https://openrouter.ai/api/v1"),
            model=fallback_cfg.get("model", "openrouter/owl-alpha"),
            enabled=bool(fallback_cfg.get("enabled", True)),
        )
        self.hermes = HermesBridge(
            command=hermes_cfg.get("command", "hermes"),
            enabled=bool(hermes_cfg.get("enabled", True)),
            container_name=hermes_cfg.get("container_name", "wq-hermes-agent"),
            fallback_client=fallback_client,
        )
        self.deerflow = DeerFlowBridge(
            command=deer_cfg.get("command", "deerflow"),
            enabled=bool(deer_cfg.get("enabled", True)),
            config_path=deer_cfg.get("config_path") or None,
            project_root=deer_cfg.get("project_root") or None,
            gateway_container=deer_cfg.get("gateway_container", "deerflow-agent"),
            gateway_url=deer_cfg.get("gateway_url", "http://localhost:8010/api/chat/stream"),
            model=deer_cfg.get("model") or None,
            fallback_client=fallback_client,
        )
        self.task_router = TaskRouter(self.hermes, self.deerflow)
        self.store.sync_theory_catalog(THEORY_CATALOG, source="dashboard_catalog", created_by="system")
        self.performance_store.sync_theory_catalog(THEORY_CATALOG, source="dashboard_catalog", created_by="system")
        self.knowledge_base = WQKnowledgeBase(config.knowledge_root, theory_store=self.store)
        self.knowledge_base.load_all()
        self.daily_researcher = DailyResearcher(
            config.root / "knowledge_base" / "research_feeds" / "daily",
            config.settings.get("research", {}),
        )

        self.wq_scraper = WQScraper(self.client)
        self.paper_scraper = PaperScraper(config.knowledge_root / "research_papers")
        self.llm_generator = LLMGenerator(self.hermes, wq_client=self.client)
        self.genetic_engine = GeneticEngine()
        self.validator = ExpressionValidator()
        self.simulator = Simulator(self.client)
        self.quality_gate = QualityGate(config.quality_gate)
        self.auto_submitter = AutoSubmitter(
            self.client,
            self.store,
            config.settings["worldquant"]["daily_submit_limit"],
        )
        self.alpha_analyzer = AlphaAnalyzer()
        self.pattern_finder = PatternFinder()
        self.correlation_checker = CorrelationChecker()
        self.theory_evaluator = TheoryAccuracyEvaluator()
        self.local_backtester = LocalBacktester(
            config.root / "runtime" / "proxy_backtests",
            settings=self.config.settings.get("pipeline", {}).get("pre_backtest", {}),
            quality_thresholds=self.quality_gate.thresholds,
        )

    def run_once(
        self,
        strategy_type: str | None = None,
        count: int | None = None,
        submit_enabled: bool = True,
    ) -> dict[str, Any]:
        defaults = self.config.alpha_defaults
        strategy_type = strategy_type or defaults.get("strategy_type", "momentum")
        pipeline_cfg = self.config.settings["pipeline"]
        total_count = count or (
            pipeline_cfg["template_batch"] + pipeline_cfg["llm_batch"] + pipeline_cfg["genetic_batch"]
        )

        tracker = WorkflowTracker(
            self.store,
            workflow_type="pipeline",
            strategy_type=strategy_type,
            target_count=total_count,
            submit_enabled=submit_enabled,
            dry_run=self.config.dry_run,
            run_tags=self._build_run_tags(strategy_type, total_count, submit_enabled, workflow_type="pipeline"),
        )

        try:
            LOGGER.info("Running alpha pipeline for strategy=%s count=%s run_id=%s", strategy_type, total_count, tracker.run_id)
            tracker.set_stage("research", "Refreshing daily research and knowledge base.")
            research_digest = self.daily_researcher.refresh()
            self.knowledge_base.load_all()
            research_summary = self._research_market(strategy_type)
            context = self._build_context(strategy_type, research_summary, research_digest)
            digest_ref = tracker.research_artifact(
                "daily_digest",
                "Daily research digest",
                research_digest[:12000],
                query_text=strategy_type,
            )
            summary_ref = tracker.research_artifact(
                "market_summary",
                "Market research summary",
                research_summary[:12000],
                query_text=strategy_type,
            )

            tracker.set_stage("generate", "Generating and deduplicating candidate alphas.")
            candidates = self._generate_candidates(strategy_type, context, self.config.knowledge_root)
            tracker.event("generate", "INFO", "candidate_generation", f"Generated {len(candidates)} raw candidates.")
            candidates = self._deduplicate(candidates)[:total_count]
            tracker.event("generate", "INFO", "candidate_dedup", f"Kept {len(candidates)} unique candidates after deduplication.")

            tracker.set_stage("pre_backtest", "Running local proxy backtests and ranking candidates before WorldQuant simulation.")
            promoted_candidates, screened_out = self._rank_candidates_for_live_simulation(
                candidates,
                strategy_type=strategy_type,
                base_context=context,
                tracker=tracker,
                research_refs=[{"artifact_id": digest_ref, "kind": "daily_digest"}, {"artifact_id": summary_ref, "kind": "market_summary"}],
                target_count=total_count,
            )

            tracker.set_stage("simulate", "Running pre-reviews, simulation, and post-reviews.")
            evaluated, recovery_notes = self._evaluate_candidates(
                promoted_candidates,
                strategy_type=strategy_type,
                base_context=context,
                submit_enabled=submit_enabled,
                target_count=total_count,
                tracker=tracker,
                research_refs=[{"artifact_id": digest_ref, "kind": "daily_digest"}, {"artifact_id": summary_ref, "kind": "market_summary"}],
            )

            tracker.set_stage("filter", "Finalizing quality-gate outcomes and report summary.")
            summary = self.alpha_analyzer.summarize(evaluated)
            operator_patterns = self.pattern_finder.operator_frequency(
                [item.candidate for item in evaluated], top_n=8
            )
            report = {
                "run_id": tracker.run_id,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "strategy_type": strategy_type,
                "dry_run": self.config.dry_run,
                "research_summary": research_summary,
                "daily_research_digest": research_digest[:4000],
                "summary": summary,
                "operator_patterns": operator_patterns,
                "approved": [item.candidate.expression for item in evaluated if item.status in {"approved", "submitted"}],
                "failure_recovery_notes": recovery_notes,
                "pre_backtest_promoted": len(promoted_candidates),
                "pre_backtest_screened_out": screened_out,
                "tested": len(evaluated),
            }
            tracker.set_stage("store", "Persisting report and workflow summary.", status="running", payload={"tested": len(evaluated)})
            self.store.save_daily_report(datetime.now().strftime("%Y-%m-%d"), report, run_id=tracker.run_id)
            self.performance_store.save_daily_report(datetime.now().strftime("%Y-%m-%d"), report, run_id=tracker.run_id)
            self._update_memory(evaluated)
            tracker.complete(report)
            return report
        except Exception as exc:
            tracker.fail(str(exc), payload={"strategy_type": strategy_type, "target_count": total_count})
            raise

    def _research_market(self, strategy_type: str) -> str:
        router_target = self.task_router.route("research")
        if router_target == "deerflow":
            return self.deerflow.run_research(
                f"Summarize current {strategy_type} alpha ideas, common operator patterns, and failure modes."
            )

        try:
            leaderboard = self.wq_scraper.leaderboard_snapshot()
            papers = self.paper_scraper.discover_sources()
            return (
                f"Leaderboard samples: {json.dumps(leaderboard[:3])}. "
                f"Research sources discovered: {len(papers)}."
            )
        except Exception as exc:
            LOGGER.warning("Research market snapshot failed; falling back to local-only research context. error=%s", exc)
            papers = self.paper_scraper.discover_sources()
            return (
                f"External leaderboard snapshot unavailable ({exc}). "
                f"Fallback to local research only. Research sources discovered: {len(papers)}."
            )

    def _build_context(self, strategy_type: str, research_summary: str, research_digest: str) -> str:
        alpha_context = self.knowledge_base.get_alpha_context(strategy_type)
        failure_context = self.knowledge_base.get_failure_context()
        theory_context = self.knowledge_base.get_theory_context(
            f"WorldQuant theory {strategy_type} alpha signal fitness turnover liquidity momentum mean reversion"
        )

        # Recent approved motifs to avoid repetition
        recent = self.store.list_recent(limit=8)
        recent_motifs = "\n".join([r.get("expression", "")[:80] for r in recent if r.get("expression")]) or "None"

        # Extract simple regime hint from research digest
        regime_hint = ""
        lower_digest = research_digest.lower()
        if "high vol" in lower_digest or "vix" in lower_digest:
            regime_hint = "High volatility regime — prefer volatility-normalized and volume-confirmed signals."
        elif "low vol" in lower_digest or "bull" in lower_digest:
            regime_hint = "Low volatility / bull regime — momentum and trend signals tend to perform better."

        return (
            f"{alpha_context}\n\nResearch summary:\n{research_summary}\n\n"
            f"Daily research digest:\n{research_digest}\n\n"
            f"Theory context:\n{theory_context}\n\n"
            f"Failure patterns:\n{failure_context}\n\n"
            f"RECENT APPROVED MOTIFS (avoid similar):\n{recent_motifs}\n\n"
            f"REGIME GUIDANCE:\n{regime_hint or 'Normal regime — balance momentum, reversion, and volume signals.'}"
        )

    def add_or_update_theory(
        self,
        theory_id: str,
        *,
        domain: str,
        title: str,
        sector_tags: list[str],
        core_principle: str,
        alpha_implication: list[str],
        example_expression: str,
        agent_reasoning: list[str],
        source: str = "agent_generated",
        created_by: str = "agent",
        status: str = "active",
    ) -> None:
        self.store.upsert_theory_entry(
            theory_id,
            domain=domain,
            title=title,
            sector_tags=sector_tags,
            core_principle=core_principle,
            alpha_implication=alpha_implication,
            example_expression=example_expression,
            agent_reasoning=agent_reasoning,
            source=source,
            created_by=created_by,
            status=status,
        )
        self.knowledge_base.load_all()

    def _generate_candidates(self, strategy_type: str, context: str, knowledge_root: Path | None = None) -> list[AlphaCandidate]:
        pipeline_cfg = self.config.settings["pipeline"]
        llm_candidates = self.llm_generator.generate(
            strategy_type, pipeline_cfg["llm_batch"], context, knowledge_root=knowledge_root
        )
        genetic_candidates = self.genetic_engine.evolve(
            llm_candidates,
            pipeline_cfg["genetic_batch"],
        )
        return llm_candidates + genetic_candidates

    def _generate_with_retry(
        self,
        strategy_type: str,
        base_context: str,
        research_refs: list[dict[str, Any]] | None,
        tracker: WorkflowTracker | None = None,
    ) -> AlphaCandidate | None:
        """
        Generate an alpha with DeerFlow pre-simulation review.
        If DeerFlow gives FAIL or metrics are too low, retry up to MAX_GENERATION_RETRIES.
        After 3 failures, research new theory and try one more time with different approach.
        """
        attempt = 0
        while attempt < self.MAX_GENERATION_RETRIES:
            attempt += 1

            # Generate new candidate
            candidates = self._generate_candidates(strategy_type, base_context)
            if not candidates:
                continue

            candidate = candidates[0]

            # Pre-simulation review by DeerFlow
            review = self.deerflow.review_alpha(
                candidate, "pre_simulation", base_context,
                knowledge_root=self.config.knowledge_root
            )

            # Simulate to get metrics
            metrics = self.simulator.run(candidate)
            history = self.store.list_recent(limit=300)
            metrics.self_correlation = max(
                metrics.self_correlation,
                self.correlation_checker.estimate_self_correlation(candidate, history),
            )

            is_too_low = (metrics.sharpe < self.LOW_METRIC_THRESHOLD and
                          metrics.fitness < self.LOW_METRIC_THRESHOLD)

            if review.verdict == "FAIL" or is_too_low:
                if tracker:
                    tracker.event(
                        "generate",
                        "WARN",
                        "deerflow_rejected",
                        f"Attempt {attempt}: DeerFlow={review.verdict}, Sharpe={metrics.sharpe:.2f}, Fitness={metrics.fitness:.2f}",
                        alpha_expression=candidate.expression,
                    )
                # Retry with new research if last attempt
                if attempt >= self.MAX_GENERATION_RETRIES - 1:
                    # Research new theory
                    new_theory = self.hermes.research_new_theory(
                        f"better {strategy_type} alpha with higher sharpe and fitness",
                        self.config.knowledge_root
                    )
                    base_context += f"\n\nNEW RESEARCH INSIGHT:\n{new_theory}"
                continue

            # Good candidate found
            return candidate

        return None

    @staticmethod
    def _pre_backtest_metrics(result: Any) -> SimulationMetrics:
        estimated = result.estimated_metrics
        return SimulationMetrics(
            sharpe=float(estimated.sharpe),
            fitness=float(estimated.fitness),
            annual_returns=float(estimated.annual_returns),
            turnover=float(estimated.turnover),
            drawdown=float(estimated.drawdown),
            self_correlation=float(estimated.self_correlation),
            notes="Local proxy backtest metrics before WorldQuant simulation.",
        )

    def _persist_screened_candidate(
        self,
        candidate: AlphaCandidate,
        result: Any,
        *,
        tracker: WorkflowTracker | None,
        base_context: str,
        research_refs: list[dict[str, Any]] | None,
    ) -> None:
        metrics = self._pre_backtest_metrics(result)

        # Auto sign-flip if both Sharpe and Fitness are strongly negative (< -1.25)
        if metrics.sharpe < -1.25 and metrics.fitness < -1.25:
            flipped_expr = f"-{candidate.expression}" if not candidate.expression.startswith("-") else candidate.expression[1:]
            if flipped_expr != candidate.expression:
                flipped_candidate = AlphaCandidate(
                    expression=flipped_expr,
                    source=candidate.source,
                    strategy_type=candidate.strategy_type,
                    rationale="Auto sign-flipped from strongly negative result",
                    metadata={**candidate.metadata, "sign_flipped": True, "original_expression": candidate.expression},
                )
                flipped_result = self.local_backtester.evaluate(flipped_candidate, self.store.list_recent(limit=300))
                if flipped_result.passed or (flipped_result.estimated_metrics.get("sharpe", -10) > -1.0 and flipped_result.estimated_metrics.get("fitness", -10) > -0.8):
                    # Persist the flipped version instead
                    self._persist_screened_candidate(
                        flipped_candidate, flipped_result,
                        tracker=tracker, base_context=base_context, research_refs=research_refs
                    )
                    return
        reasons = result.reasons or [f"Composite local backtest score {result.score:.2f} did not qualify for live simulation."]
        status = "screened_out"
        alpha_run_id = self.store.insert_alpha(
            candidate,
            metrics,
            status,
            notes="; ".join(reasons),
            run_id=tracker.run_id if tracker else None,
            generation_source=self._generation_source(candidate),
            origin_agent=self._origin_agent(candidate),
            run_tags=self._candidate_run_tags(candidate, tracker.run_id if tracker else None),
            gate_failure_reason=reasons[0] if reasons else None,
            pre_backtest_score=float(result.score),
            pre_backtest_passed=False,
            pre_backtest_metrics=self.local_backtester.as_payload(result).get("estimated_metrics", {}),
        )
        if tracker is not None:
            tracker.alpha_explanation(
                alpha_run_id,
                candidate,
                thresholds=self.quality_gate.thresholds,
                prompt_context=base_context,
                research_refs=research_refs,
                stage_notes={
                    "status": status,
                    "pre_backtest": self.local_backtester.as_payload(result),
                    "gate_reasons": reasons,
                },
            )
            tracker.event(
                "pre_backtest",
                "WARNING",
                "prebacktest_blocked",
                "Candidate blocked before WorldQuant simulation.",
                alpha_expression=candidate.expression,
                alpha_run_id=alpha_run_id,
                payload=self.local_backtester.as_payload(result),
            )

    def _rank_candidates_for_live_simulation(
        self,
        candidates: list[AlphaCandidate],
        *,
        strategy_type: str,
        base_context: str,
        tracker: WorkflowTracker | None,
        research_refs: list[dict[str, Any]] | None,
        target_count: int,
    ) -> tuple[list[AlphaCandidate], int]:
        del strategy_type
        history = self.store.list_recent(limit=300)
        max_promoted = min(target_count, self.local_backtester.max_live_candidates)
        promoted, blocked = self.local_backtester.rank_candidates(candidates, history, max_promoted=max_promoted)
        if tracker is not None:
            tracker.event(
                "pre_backtest",
                "INFO",
                "prebacktest_ranked",
                f"Local proxy backtest promoted {len(promoted)} of {len(candidates)} candidates.",
                payload={
                    "promoted": len(promoted),
                    "blocked": len(blocked),
                    "max_live_candidates": max_promoted,
                },
            )
        for candidate, result in promoted:
            if tracker is not None:
                tracker.event(
                    "pre_backtest",
                    "INFO",
                    "prebacktest_promoted",
                    f"Promoted candidate for live simulation with local score {result.score:.2f}.",
                    alpha_expression=candidate.expression,
                    payload=self.local_backtester.as_payload(result),
                )
        for candidate, result in blocked:
            metrics = self._pre_backtest_metrics(result)
            # If pre-backtest is strongly negative → flip sign and simulate directly
            if metrics.sharpe < -1.25 and metrics.fitness < -1.0:
                flipped_expr = f"-{candidate.expression}" if not candidate.expression.startswith("-") else candidate.expression[1:]
                if flipped_expr != candidate.expression:
                    flipped_candidate = AlphaCandidate(
                        expression=flipped_expr,
                        source=candidate.source,
                        strategy_type=candidate.strategy_type,
                        rationale="Sign-flipped for direct live simulation (pre-backtest strongly negative)",
                        metadata={**candidate.metadata, "sign_flipped": True, "original_expression": candidate.expression},
                    )
                    # Directly simulate the flipped version (bypass pre-backtest)
                    self._simulate_and_store(flipped_candidate, tracker=tracker, base_context=base_context, research_refs=research_refs)
                    continue
            # Normal screening path
            self._persist_screened_candidate(
                candidate,
                result,
                tracker=tracker,
                base_context=base_context,
                research_refs=research_refs,
            )
        return [candidate for candidate, _ in promoted], len(blocked)

    MAX_GENERATION_RETRIES = 3
    LOW_METRIC_THRESHOLD = -0.8   # If both Sharpe and Fitness below this → reject

    def _simulate_and_store(
        self,
        candidate: AlphaCandidate,
        *,
        tracker: WorkflowTracker | None,
        base_context: str,
        research_refs: list[dict[str, Any]] | None,
    ) -> None:
        """Directly simulate a candidate (bypass pre-backtest) and store result.
        If DeerFlow pre-review fails or metrics are too low, retry generation.
        """
        # Pre-simulation DeerFlow review + retry logic
        final_candidate = self._generate_with_retry(
            candidate.strategy_type,
            base_context,
            research_refs,
            tracker=tracker,
        ) or candidate   # fallback to original if retry fails

        metrics = self.simulator.run(final_candidate)
        history = self.store.list_recent(limit=300)
        metrics.self_correlation = max(
            metrics.self_correlation,
            self.correlation_checker.estimate_self_correlation(final_candidate, history),
        )
        gate_reasons = self.quality_gate.evaluate(metrics)
        status = "approved" if not gate_reasons else "tested"

        pre_reviews = [
            self.hermes.review_alpha(final_candidate, "pre_simulation", base_context, knowledge_root=self.config.knowledge_root),
            self.deerflow.review_alpha(final_candidate, "pre_simulation", base_context, knowledge_root=self.config.knowledge_root),
        ]
        post_reviews = [
            self.hermes.review_alpha(final_candidate, "post_simulation", base_context, metrics, knowledge_root=self.config.knowledge_root),
            self.deerflow.review_alpha(final_candidate, "post_simulation", base_context, metrics, knowledge_root=self.config.knowledge_root),
        ]

        notes = "; ".join(
            gate_reasons
            + [f"{r.agent}:{r.stage}:{r.verdict}" for r in pre_reviews + post_reviews]
        )

        alpha_run_id = self.store.insert_alpha(
            final_candidate,
            metrics,
            status,
            notes=notes,
            run_id=tracker.run_id if tracker else None,
            generation_source=self._generation_source(final_candidate),
            origin_agent=self._origin_agent(final_candidate),
            pre_sim_confidence=average_stage_confidence(pre_reviews, "pre_simulation"),
            post_sim_confidence=average_stage_confidence(post_reviews, "post_simulation"),
            pre_sim_verdict=aggregate_stage_verdict(pre_reviews, "pre_simulation"),
            post_sim_verdict=aggregate_stage_verdict(post_reviews, "post_simulation"),
            run_tags=self._candidate_run_tags(candidate, tracker.run_id if tracker else None),
            gate_failure_reason=gate_reasons[0] if gate_reasons else None,
            pre_backtest_score=None,
            pre_backtest_passed=None,
            pre_backtest_metrics={},
        )

        # Record theory accuracy for applied theories
        self.theory_evaluator.record_theory_application(
            theory_name="volume_correlation" if "volume" in final_candidate.expression.lower() else "general",
            sharpe=metrics.sharpe,
            fitness=metrics.fitness,
            turnover=metrics.turnover,
        )

        if tracker is not None:
            tracker.alpha_explanation(
                alpha_run_id,
                candidate,
                thresholds=self.quality_gate.thresholds,
                prompt_context=base_context,
                research_refs=research_refs,
                stage_notes={
                    "status": status,
                    "direct_simulation": True,
                    "sign_flipped": True,
                },
            )

    def _evaluate_candidates(
        self,
        candidates: list[AlphaCandidate],
        strategy_type: str,
        base_context: str,
        submit_enabled: bool,
        target_count: int,
        tracker: WorkflowTracker | None = None,
        research_refs: list[dict[str, Any]] | None = None,
    ) -> tuple[list[EvaluatedAlpha], list[str]]:
        evaluated: list[EvaluatedAlpha] = []
        recovery_notes: list[str] = []
        history = self.store.list_recent(limit=200)
        queue: deque[AlphaCandidate] = deque(candidates)
        alpha_run_id = None
        final_candidate = None  # Initialize to avoid NameError
        seen_expressions = {item["expression"] for item in history if item.get("expression")}
        recovery_budget = int(self.config.settings["pipeline"].get("failure_recovery_max_attempts", 2))
        max_total = target_count + max(recovery_budget, 0)

        while queue and len(evaluated) < max_total:
            candidate = queue.popleft()
            if candidate.expression in seen_expressions:
                continue
            seen_expressions.add(candidate.expression)
            if tracker is not None:
                tracker.event(
                    "simulate",
                    "INFO",
                    "candidate_started",
                    f"Evaluating candidate {len(evaluated) + 1}/{max_total}.",
                    alpha_expression=candidate.expression,
                    payload={"metadata": candidate.metadata},
                )

            errors = self.validator.validate(candidate.expression)
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
                item = EvaluatedAlpha(
                    candidate=candidate,
                    metrics=metrics,
                    validation_errors=errors,
                    gate_passed=False,
                    gate_reasons=errors,
                    status="invalid",
                )
                alpha_run_id = self.store.insert_alpha(
                    candidate,
                    metrics,
                    item.status,
                    notes="; ".join(errors),
                    run_id=tracker.run_id if tracker else None,
                    agent_reviews=[],
                    generation_source=self._generation_source(candidate),
                    origin_agent=self._origin_agent(candidate),
                    run_tags=self._candidate_run_tags(candidate, tracker.run_id if tracker else None),
                    gate_failure_reason=errors[0] if errors else None,
                )
                if tracker is not None:
                    tracker.alpha_explanation(
                        alpha_run_id,
                        candidate,
                        thresholds=self.quality_gate.thresholds,
                        prompt_context=base_context,
                        research_refs=research_refs,
                        stage_notes={"validation_errors": errors},
                    )
                    tracker.event(
                        "simulate",
                        "ERROR",
                        "candidate_invalid",
                        "Candidate failed validation before simulation.",
                        alpha_expression=candidate.expression,
                        alpha_run_id=alpha_run_id,
                        payload={"errors": errors},
                )
                evaluated.append(item)
                recovery_budget = self._queue_recovery_candidate(
                    strategy_type,
                    base_context,
                    candidate,
                    errors,
                    queue,
                    recovery_notes,
                    recovery_budget,
                    seen_expressions,
                    history,
                    tracker,
                    research_refs,
                )
                continue

            pre_backtest = self.local_backtester.evaluate(candidate, history)
            if not pre_backtest.passed:
                self._persist_screened_candidate(
                    candidate,
                    pre_backtest,
                    tracker=tracker,
                    base_context=base_context,
                    research_refs=research_refs,
                )
                evaluated.append(
                    EvaluatedAlpha(
                        candidate=candidate,
                        metrics=self._pre_backtest_metrics(pre_backtest),
                        gate_passed=False,
                        gate_reasons=list(pre_backtest.reasons),
                        status="screened_out",
                    )
                )
                recovery_budget = self._queue_recovery_candidate(
                    strategy_type,
                    base_context,
                    candidate,
                    list(pre_backtest.reasons),
                    queue,
                    recovery_notes,
                    recovery_budget,
                    seen_expressions,
                    history,
                    tracker,
                    research_refs,
                )
                continue

            agent_reviews = self._agent_reviews(candidate, "pre_simulation", candidate.expression)
            pre_failures = [review for review in agent_reviews if review.verdict == "FAIL"]
            pre_gate_reasons = [f"{review.agent} pre-review: {review.verdict}" for review in pre_failures]
            if tracker is not None:
                tracker.event(
                    "simulate",
                    "INFO",
                    "pre_review",
                    "Completed pre-simulation reviews.",
                    alpha_expression=candidate.expression,
                    payload={"reviews": [asdict(review) for review in agent_reviews]},
                )

            try:
                metrics = self.simulator.run(candidate)
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
                gate_reasons = [f"Simulation failed: {exc}"]
                item = EvaluatedAlpha(
                    candidate=candidate,
                    metrics=metrics,
                    gate_passed=False,
                    gate_reasons=gate_reasons,
                    status="tested",
                    agent_reviews=agent_reviews,
                )
                alpha_run_id = self.store.insert_alpha(
                    candidate,
                    metrics,
                    item.status,
                    notes="; ".join(gate_reasons),
                    run_id=tracker.run_id if tracker else None,
                    agent_reviews=[asdict(review) for review in agent_reviews],
                    generation_source=self._generation_source(candidate),
                    origin_agent=self._origin_agent(candidate),
                    pre_sim_confidence=average_stage_confidence(agent_reviews, "pre_simulation"),
                    pre_sim_verdict=aggregate_stage_verdict(agent_reviews, "pre_simulation"),
                    run_tags=self._candidate_run_tags(candidate, tracker.run_id if tracker else None),
                    gate_failure_reason=gate_reasons[0] if gate_reasons else None,
                    pre_backtest_score=float(pre_backtest.score),
                    pre_backtest_passed=bool(pre_backtest.passed),
                    pre_backtest_metrics=self.local_backtester.as_payload(pre_backtest).get("estimated_metrics", {}),
                )
                if tracker is not None:
                    tracker.alpha_explanation(
                        alpha_run_id,
                        candidate,
                        thresholds=self.quality_gate.thresholds,
                        prompt_context=base_context,
                        research_refs=research_refs,
                        agent_reviews=agent_reviews,
                        stage_notes={"simulation_error": gate_reasons, "pre_backtest": self.local_backtester.as_payload(pre_backtest)},
                    )
                    tracker.event(
                        "simulate",
                        "ERROR",
                        "candidate_failed",
                        "Simulation failed for candidate.",
                        alpha_expression=candidate.expression,
                        alpha_run_id=alpha_run_id,
                        payload={"reasons": gate_reasons},
                    )
                evaluated.append(item)
                history.append({"expression": candidate.expression})
                recovery_budget = self._queue_recovery_candidate(
                    strategy_type,
                    base_context,
                    candidate,
                    gate_reasons,
                    queue,
                    recovery_notes,
                    recovery_budget,
                    seen_expressions,
                    history,
                    tracker,
                    research_refs,
                )
                continue
            metrics.self_correlation = max(
                metrics.self_correlation,
                self.correlation_checker.estimate_self_correlation(candidate, history),
            )
            post_reviews = self._agent_reviews(candidate, "post_simulation", metrics.notes or candidate.expression, metrics)
            agent_reviews.extend(post_reviews)
            gate_assessment = self.quality_gate.assess(metrics)
            gate_failures = gate_assessment["failures"]
            gate_warnings = gate_assessment["warnings"]
            gate_reasons = pre_gate_reasons + [str(item["message"]) for item in gate_failures]
            gate_reasons.extend(
                f"{review.agent} post-review: {review.verdict}"
                for review in post_reviews
                if review.verdict == "FAIL"
            )
            gate_passed = not gate_reasons
            needs_review = gate_passed and bool(gate_warnings)
            status = "approved" if gate_passed else "tested"
            submitted_at: str | None = None

            if gate_passed and submit_enabled:
                if tracker is not None:
                    tracker.event(
                        "submit",
                        "INFO",
                        "submit_attempt",
                        "Attempting submission for passing alpha.",
                        alpha_expression=candidate.expression,
                    )
                submitted, result = self.auto_submitter.submit(candidate)
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
                agent_reviews=agent_reviews,
            )
            alpha_run_id = self.store.insert_alpha(
                candidate,
                metrics,
                status,
                notes="; ".join(gate_reasons),
                run_id=tracker.run_id if tracker else None,
                agent_reviews=[asdict(review) for review in agent_reviews],
                generation_source=self._generation_source(candidate),
                origin_agent=self._origin_agent(candidate),
                pre_sim_confidence=average_stage_confidence(agent_reviews, "pre_simulation"),
                post_sim_confidence=average_stage_confidence(agent_reviews, "post_simulation"),
                pre_sim_verdict=aggregate_stage_verdict(agent_reviews, "pre_simulation"),
                post_sim_verdict=aggregate_stage_verdict(agent_reviews, "post_simulation"),
                run_tags=self._candidate_run_tags(candidate, tracker.run_id if tracker else None),
                gate_failure_reason=gate_reasons[0] if gate_reasons else None,
                needs_review=needs_review,
                submitted_at=submitted_at,
                pre_backtest_score=float(pre_backtest.score),
                pre_backtest_passed=bool(pre_backtest.passed),
                pre_backtest_metrics=self.local_backtester.as_payload(pre_backtest).get("estimated_metrics", {}),
            )
        if tracker is not None:
            tracker.alpha_explanation(
                alpha_run_id,
                final_candidate,
                thresholds=self.quality_gate.thresholds,
                prompt_context=base_context,
                research_refs=research_refs,
                agent_reviews=agent_reviews,
                stage_notes={
                    "pre_backtest": self.local_backtester.as_payload(pre_backtest),
                    "gate_reasons": gate_reasons,
                    "gate_failures": gate_failures,
                    "gate_warnings": gate_warnings,
                    "needs_review": needs_review,
                    "status": status,
                    "metrics": asdict(metrics),
                },
            )
            for failure in gate_failures:
                tracker.event(
                    "filter",
                    "WARNING",
                    "GATE_FAIL",
                    str(failure["message"]),
                    alpha_expression=final_candidate.expression,
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
                    f"Candidate finished with status={status}.",
                    alpha_expression=candidate.expression,
                    alpha_run_id=alpha_run_id,
                    payload={"gate_reasons": gate_reasons, "gate_warnings": gate_warnings, "needs_review": needs_review, "metrics": asdict(metrics)},
                )
            evaluated.append(item)
            history.append({"expression": candidate.expression})
            if not gate_passed:
                recovery_budget = self._queue_recovery_candidate(
                    strategy_type,
                    base_context,
                    candidate,
                    gate_reasons,
                    queue,
                    recovery_notes,
                    recovery_budget,
                    seen_expressions,
                    history,
                    tracker,
                    research_refs,
                )

        return evaluated, recovery_notes

    def _queue_recovery_candidate(
        self,
        strategy_type: str,
        base_context: str,
        failed_candidate: AlphaCandidate,
        failure_reasons: list[str],
        queue: deque[AlphaCandidate],
        recovery_notes: list[str],
        recovery_budget: int,
        seen_expressions: set[str],
        history: list[dict[str, Any]],
        tracker: WorkflowTracker | None,
        research_refs: list[dict[str, Any]] | None,
    ) -> int:
        if recovery_budget <= 0:
            return recovery_budget

        recovery_candidate, recovery_note = self._recover_from_failure(
            strategy_type=strategy_type,
            failed_candidate=failed_candidate,
            failure_reasons=failure_reasons,
            base_context=base_context,
        )
        if recovery_note:
            recovery_notes.append(recovery_note)
        if recovery_candidate is not None and recovery_candidate.expression not in seen_expressions:
            pre_backtest = self.local_backtester.evaluate(recovery_candidate, history)
            if pre_backtest.passed:
                queue.append(recovery_candidate)
                if tracker is not None:
                    tracker.event(
                        "pre_backtest",
                        "INFO",
                        "prebacktest_promoted",
                        f"Promoted recovery candidate with local score {pre_backtest.score:.2f}.",
                        alpha_expression=recovery_candidate.expression,
                        payload=self.local_backtester.as_payload(pre_backtest),
                    )
            else:
                self._persist_screened_candidate(
                    recovery_candidate,
                    pre_backtest,
                    tracker=tracker,
                    base_context=base_context,
                    research_refs=research_refs,
                )
            return recovery_budget - 1
        return recovery_budget

    def _recover_from_failure(
        self,
        strategy_type: str,
        failed_candidate: AlphaCandidate,
        failure_reasons: list[str],
        base_context: str,
    ) -> tuple[AlphaCandidate | None, str]:
        del base_context
        tag = re.sub(r"[^a-z0-9]+", "-", strategy_type.lower()).strip("-") or "alpha"
        topics = [
            f"WorldQuant Brain {strategy_type} alpha",
            f"{strategy_type} factor investing market regime",
        ]
        topics.extend(reason[:80] for reason in failure_reasons[:2])
        market_research = self.daily_researcher.targeted_research(topics, tag=tag)
        paper_digests = self.paper_scraper.build_paper_digest(
            f"{strategy_type} {' '.join(failure_reasons[:3])}",
            limit=1,
        )

        paper_section_lines = ["## Paper Lessons", ""]
        for paper in paper_digests:
            paper_section_lines.append(f"### {paper['name']}")
            paper_section_lines.append(f"Source: {paper['path']}")
            paper_section_lines.append("")
            paper_section_lines.append(paper["excerpt"])
            paper_section_lines.append("")
        paper_section = "\n".join(paper_section_lines).strip()

        remediation_prompt = (
            f"A WorldQuant alpha failed.\n"
            f"Failed expression: {failed_candidate.expression}\n"
            f"Failure reasons: {'; '.join(failure_reasons)}\n\n"
            f"Market research:\n{market_research[:5000]}\n\n"
            f"{paper_section}\n\n"
            "Write a short remediation note with concrete operator, turnover, correlation, and drawdown adjustments. "
            "Then provide one improved expression on a final line prefixed with EXPRESSION: . "
            "Use only rank, zscore, ts_mean, ts_delta, ts_std_dev, ts_corr, close, returns, volume, vwap."
        )
        remediation = self.hermes.ask(remediation_prompt).strip()
        note_path = self._write_failure_recovery_note(
            strategy_type=strategy_type,
            failed_candidate=failed_candidate,
            failure_reasons=failure_reasons,
            market_research=market_research,
            paper_section=paper_section,
            remediation=remediation,
        )
        self.knowledge_base.load_all()

        expression = self._extract_recovery_expression(remediation)
        if not expression:
            return None, str(note_path)
        return (
            AlphaCandidate(
                expression=expression,
                source="failure_recovery",
                strategy_type=strategy_type,
                rationale=f"Refined after failure analysis for {failed_candidate.expression}.",
                metadata={
                    **failed_candidate.metadata,
                    "generation_source": "failure_recovery",
                    "origin_agent": "hermes",
                    "recovery_note": str(note_path),
                },
            ),
            str(note_path),
        )

    def _write_failure_recovery_note(
        self,
        strategy_type: str,
        failed_candidate: AlphaCandidate,
        failure_reasons: list[str],
        market_research: str,
        paper_section: str,
        remediation: str,
    ) -> Path:
        recovery_root = self.config.knowledge_root / "lessons_learned" / "failure_recovery"
        recovery_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_strategy = re.sub(r"[^a-z0-9]+", "-", strategy_type.lower()).strip("-") or "alpha"
        out_path = recovery_root / f"{stamp}_{safe_strategy}.md"
        content = (
            f"# Failure Recovery Note - {strategy_type}\n\n"
            f"## Failed Expression\n{failed_candidate.expression}\n\n"
            f"## Failure Reasons\n- " + "\n- ".join(failure_reasons) + "\n\n"
            f"## Market Research\n{market_research}\n\n"
            f"{paper_section}\n\n"
            f"## Applied Lessons\n{remediation}\n"
        )
        out_path.write_text(content, encoding="utf-8")
        return out_path

    def _update_memory(self, evaluated: list[EvaluatedAlpha]) -> None:
        works_path = self.config.knowledge_root / "lessons_learned" / "what_works.md"
        fails_path = self.config.knowledge_root / "lessons_learned" / "what_fails.md"
        works_lines: list[str] = []
        fail_lines: list[str] = []
        memory_lines: list[str] = []

        for item in evaluated:
            lesson = (
                f"{item.candidate.expression} | status={item.status} | "
                f"sharpe={item.metrics.sharpe:.2f} | fitness={item.metrics.fitness:.2f}"
            )
            memory_lines.append(lesson)
            if item.status in {"approved", "submitted"}:
                works_lines.append(f"- {lesson}")
            elif item.status in {"tested", "invalid"}:
                fail_lines.append(f"- {lesson} | notes={'; '.join(item.gate_reasons or item.validation_errors)}")

        if works_lines:
            with works_path.open("a", encoding="utf-8") as handle:
                handle.write("\n" + "\n".join(works_lines) + "\n")
        if fail_lines:
            with fails_path.open("a", encoding="utf-8") as handle:
                handle.write("\n" + "\n".join(fail_lines) + "\n")

        if memory_lines:
            self.hermes.remember("\n".join(memory_lines))

    def _build_run_tags(
        self,
        strategy_type: str,
        target_count: int,
        submit_enabled: bool,
        *,
        workflow_type: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pipeline_cfg = self.config.settings.get("pipeline", {})
        return {
            "workflow_type": workflow_type,
            "strategy_type": strategy_type,
            "target_count": target_count,
            "submit_enabled": submit_enabled,
            "dry_run": self.config.dry_run,
            "enable_research": bool(pipeline_cfg.get("enable_research", True)),
            "self_critique_rounds": int(pipeline_cfg.get("self_critique_rounds", 2)),
            "pre_simulation_review": bool(pipeline_cfg.get("pre_simulation_review", True)),
            "post_simulation_review": bool(pipeline_cfg.get("post_simulation_review", True)),
            "template_batch": int(pipeline_cfg.get("template_batch", 0)),
            "llm_batch": int(pipeline_cfg.get("llm_batch", 0)),
            "genetic_batch": int(pipeline_cfg.get("genetic_batch", 0)),
            **(extra or {}),
        }

    @staticmethod
    def _generation_source(candidate: AlphaCandidate) -> str:
        source = str(candidate.metadata.get("generation_source") or candidate.source or "unknown").strip()
        return source or "unknown"

    @staticmethod
    def _origin_agent(candidate: AlphaCandidate) -> str | None:
        explicit = str(candidate.metadata.get("origin_agent") or "").strip()
        if explicit:
            return explicit
        source = str(candidate.source or "").lower()
        if source in {"llm", "hermes", "hermes_llm"}:
            return "hermes"
        if source in {"deerflow", "deerflow_llm"}:
            return "deerflow"
        if source == "react_ui":
            return "studio"
        return None

    def _candidate_run_tags(self, candidate: AlphaCandidate, run_id: str | None) -> dict[str, Any]:
        return {
            "run_id": run_id,
            "strategy_type": candidate.strategy_type,
            "source": candidate.source,
            "generation_source": self._generation_source(candidate),
            "origin_agent": self._origin_agent(candidate),
        }

    def _agent_reviews(
        self,
        candidate: AlphaCandidate,
        stage: str,
        context: str,
        metrics: SimulationMetrics | None = None,
    ) -> list[AgentReview]:
        reviews: list[AgentReview] = []
        enabled = (
            self.config.settings["pipeline"].get("pre_simulation_review", True)
            if stage == "pre_simulation"
            else self.config.settings["pipeline"].get("post_simulation_review", True)
        )
        if enabled:
            reviews.append(self.hermes.review_alpha(candidate, stage, context, metrics, knowledge_root=self.config.knowledge_root))
            reviews.append(self.deerflow.review_alpha(candidate, stage, context, metrics, knowledge_root=self.config.knowledge_root))
        return reviews

    @staticmethod
    def _extract_recovery_expression(remediation: str) -> str:
        for line in remediation.splitlines():
            stripped = line.strip()
            if stripped.upper().startswith("EXPRESSION:"):
                return stripped.split(":", 1)[1].strip()
        return ""

    @staticmethod
    def _deduplicate(candidates: list[AlphaCandidate]) -> list[AlphaCandidate]:
        seen: set[str] = set()
        unique: list[AlphaCandidate] = []
        for candidate in candidates:
            if candidate.expression in seen:
                continue
            seen.add(candidate.expression)
            unique.append(candidate)
        return unique

    def get_theory_accuracy_report(self) -> Dict[str, Any]:
        """Return current theory performance evaluation."""
        return self.theory_evaluator.evaluate()
