from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from pipeline.models import AlphaCandidate
from pipeline.generator.expression_validator import ExpressionValidator
from orchestration import DeerFlowBridge
from knowledge_base.alpha_theory_rag import get_theory_context_for_generation
from knowledge_base.data_researcher import DataResearcher
from knowledge_base.wq_docs_rag import get_wq_docs_context


# Whitelist of official WorldQuant Brain operators. Mirrors the catalog in
# docs/wq_brain/operators.md. The extractor only accepts a line as a candidate
# FASTEXPR if it calls at least one of these names. Keep this list in sync
# with the markdown reference; do NOT add invented operator names.
OFFICIAL_OPERATORS: tuple[str, ...] = (
    # Arithmetic
    "add", "subtract", "multiply", "divide", "power", "abs", "sign", "log",
    "exp", "sqrt", "inverse", "min", "max", "signed_power", "s_log_1p",
    # Logical
    "less", "greater", "equal", "not_equal", "less_equal", "greater_equal",
    "and", "or", "not", "if_else",
    # Cross-sectional
    "rank", "zscore", "scale", "normalize", "quantile", "winsorize",
    "truncate", "vector_neut", "regression_neut", "pareto",
    # Time-series
    "ts_mean", "ts_sum", "ts_std_dev", "ts_var", "ts_median", "ts_min",
    "ts_max", "ts_arg_min", "ts_arg_max", "ts_delta", "ts_delay",
    "ts_returns", "ts_rank", "ts_zscore", "ts_scale", "ts_corr",
    "ts_covariance", "ts_co_skewness", "ts_co_kurtosis", "ts_skewness",
    "ts_kurtosis", "ts_decay_linear", "ts_decay_exp_window", "ts_product",
    "ts_count_nans", "hump", "jump_decay",
    # Group
    "group_mean", "group_neutralize", "group_rank", "group_zscore",
    "group_normalize", "group_scale", "group_sum", "group_count",
    "group_max", "group_min", "group_median", "group_std_dev",
    "group_percentage", "group_backfill",
    # Transformational
    "trade_when", "pasteurize", "densify", "clamp",
    # Vector
    "vec_avg", "vec_sum", "vec_count", "vec_max", "vec_min", "vec_argmax",
    "vec_argmin", "vec_choose", "vec_norm",
)

OPERATOR_CALL = re.compile(
    r"\b(?:" + "|".join(OFFICIAL_OPERATORS) + r")\s*\("
)


class LLMGenerator:
    def __init__(self, deerflow: DeerFlowBridge, wq_client: Any | None = None) -> None:
        self.deerflow = deerflow
        self.wq_client = wq_client
        self.validator = ExpressionValidator()

    def _extract_expressions(self, raw_output: str, count: int) -> list[str]:
        expressions: list[str] = []
        seen: set[str] = set()
        for raw_line in raw_output.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("```"):
                continue
            line = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
            line = line.strip("`").strip()
            if not OPERATOR_CALL.search(line):
                continue
            if self.validator.validate(line):
                continue
            canonical = re.sub(r"\s+", "", line)
            if canonical in seen:
                continue
            seen.add(canonical)
            expressions.append(line)
            if len(expressions) >= count:
                break
        return expressions

    def generate(
        self,
        strategy_type: str,
        count: int,
        context: str,
        knowledge_root: Path | None = None,
    ) -> list[AlphaCandidate]:
        theory_rag = ""
        data_context = ""
        if knowledge_root:
            theory_rag = get_theory_context_for_generation(knowledge_root, strategy_type)
            data_researcher = DataResearcher(knowledge_root, wq_client=self.wq_client)
            data_context = data_researcher.build_data_context(strategy_type)
        wq_docs = get_wq_docs_context(
            f"WorldQuant Brain operators catalog reference {strategy_type} "
            "ts_mean ts_delta ts_rank ts_corr ts_decay_linear rank zscore "
            "group_neutralize trade_when neutralization decay turnover",
            k=4,
        )

        operator_whitelist = ", ".join(OFFICIAL_OPERATORS)
        prompt = (
            f"Generate {count} novel WorldQuant FASTEXPR alphas for {strategy_type}.\n\n"
            "=== MANDATORY RULES (from https://platform.worldquantbrain.com/learn/operators) ===\n"
            "- Use ONLY operators from the official WorldQuant Brain catalog below. "
            "Do NOT invent operator names (e.g. rank1, ts_log_returns, mean_rev are FORBIDDEN).\n"
            f"- OFFICIAL OPERATORS: {operator_whitelist}\n"
            "- Lookbacks `d` MUST be one of: 5, 10, 20, 60. Any other window is rejected.\n"
            "- Prefer ts_* operators for any rolling aggregation; never roll your own mean/std.\n"
            "- For neutralization use group_neutralize(x, subindustry) or rely on the "
            "simulate-level neutralization=SUBINDUSTRY.\n"
            "- For turnover control use ts_decay_linear, ts_decay_exp_window, hump, or trade_when.\n"
            "- Optimize FIRST for Fitness = Sharpe x sqrt(|returns| / max(turnover, 0.125)).\n"
            "- Must include at least one volume component (volume, vwap, adv20, "
            "ts_corr(close, volume, d), ...) unless the strategy is pure price momentum.\n"
            "- Avoid near-duplicates of recently approved alphas.\n"
            "- Output: exactly ONE clean expression per line. No markdown, no explanation.\n\n"
            "=== 0. WORLDQUANT BRAIN DOCS (authoritative) ===\n"
            f"{wq_docs or '(no WQ Brain docs indexed; see docs/wq_brain/README.md)'}\n\n"
            "=== 1. THEORY GROUNDING (RAG) ===\n"
            f"{theory_rag}\n\n"
            "=== 2. DATA UNIVERSE & LIVE REGIME (from WorldQuant Brain) ===\n"
            f"{data_context}\n\n"
            "=== 3. RESEARCH CONTEXT + RECENT MOTIFS + REGIME GUIDANCE ===\n"
            f"{context}\n\n"
            "Now generate the alphas following all rules above."
        )
        raw_output = self.deerflow.run_research(prompt)
        expressions = self._extract_expressions(raw_output, count)
        # Store theory context for transparency
        theory_used = theory_rag[:1500] if theory_rag else "No theory RAG loaded"

        return [
            AlphaCandidate(
                expression=expression,
                source="llm",
                strategy_type=strategy_type,
                rationale="LLM-generated candidate derived from RAG context.",
                metadata={
                    "generation_source": "llm_generator",
                    "origin_agent": "deerflow",
                    "delay": 1,
                    "universe": "TOP3000",
                    "truncation": 0.08,
                    "region": "USA",
                    "decay": 6,
                    "neutralization": "SUBINDUSTRY",
                    "pasteurization": "ON",
                    "nanHandling": "OFF",
                    "theory_context_used": theory_used,
                },
            )
            for expression in expressions[:count]
        ]
