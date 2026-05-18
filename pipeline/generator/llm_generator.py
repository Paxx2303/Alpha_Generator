from __future__ import annotations

from pipeline.models import AlphaCandidate
from orchestration import HermesBridge


class LLMGenerator:
    def __init__(self, hermes: HermesBridge) -> None:
        self.hermes = hermes

    def generate(
        self,
        strategy_type: str,
        count: int,
        context: str,
    ) -> list[AlphaCandidate]:
        safe_patterns = (
            "rank(ts_delta(close, N) / ts_std_dev(close, N))\n"
            "rank(close / ts_mean(close, N) - 1)\n"
            "rank(ts_corr(volume, returns, N))\n"
            "rank(volume / ts_mean(volume, N))\n"
            "rank(-ts_delta(close, N))\n"
            "rank(-ts_delta(vwap, N))"
        )
        fitness_rules = (
            "Fitness-first rules:\n"
            "- Fitness is driven by Sharpe, Returns, and Turnover.\n"
            "- If turnover is above 0.125, smoother signals usually help fitness.\n"
            "- Prefer N=20 or N=60 for fitness-first ideas unless a short-horizon edge is very clear.\n"
            "- Use N=5 or N=10 sparingly.\n"
            "- Favor diversified outputs across trend, price-vs-mean, volatility-normalized, and volume-confirmation motifs.\n"
            "- Avoid near-duplicate formulas that only differ trivially.\n"
        )
        prompt = (
            f"Generate {count} WorldQuant-style fast expressions for {strategy_type}.\n"
            "Optimize for fitness first, then Sharpe.\n"
            "Use only these operator templates and fields.\n"
            "Replace N with one lookback from 5, 10, 20, 60.\n"
            "Do not use zscore. Do not invent new functions. Do not add explanations.\n"
            f"{fitness_rules}\n"
            f"Safe patterns:\n{safe_patterns}\n"
            "Return exactly one expression per line without bullets or explanations.\n"
            f"Context:\n{context}"
        )
        raw_output = self.hermes.ask(prompt)
        expressions = [line.strip("- ").strip() for line in raw_output.splitlines() if line.strip()]
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
                },
            )
            for expression in expressions[:count]
        ]
