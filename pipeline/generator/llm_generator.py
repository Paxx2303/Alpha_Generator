from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.models import AlphaCandidate
from orchestration import HermesBridge
from knowledge_base.alpha_theory_rag import get_theory_context_for_generation
from knowledge_base.data_researcher import DataResearcher


class LLMGenerator:
    def __init__(self, hermes: HermesBridge, wq_client: Any | None = None) -> None:
        self.hermes = hermes
        self.wq_client = wq_client

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

        prompt = (
            f"Generate {count} novel WorldQuant FASTEXPR alphas for {strategy_type}.\n\n"
            "=== MANDATORY RULES ===\n"
            "- Use ONLY operators: ts_mean, ts_delta, ts_std_dev, ts_corr, rank, zscore, ts_rank\n"
            "- Lookbacks allowed: 5, 10, 20, 60\n"
            "- Optimize FIRST for Fitness = Sharpe × sqrt(|returns| / max(turnover, 0.125))\n"
            "- Must include at least one volume component (unless pure momentum)\n"
            "- Avoid near-duplicates of recently approved alphas\n"
            "- Output: exactly ONE clean expression per line. No markdown, no explanation.\n\n"
            "=== 1. THEORY GROUNDING (RAG) ===\n"
            f"{theory_rag}\n\n"
            "=== 2. DATA UNIVERSE & LIVE REGIME (from WorldQuant Brain) ===\n"
            f"{data_context}\n\n"
            "=== 3. RESEARCH CONTEXT + RECENT MOTIFS + REGIME GUIDANCE ===\n"
            f"{context}\n\n"
            "Now generate the alphas following all rules above."
        )
        raw_output = self.hermes.ask(prompt)
        expressions = [line.strip("- ").strip() for line in raw_output.splitlines() if line.strip()]
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
                    "origin_agent": "hermes",
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
