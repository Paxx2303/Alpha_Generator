from __future__ import annotations

from itertools import islice
import re

from pipeline.models import AlphaCandidate


NUMBER_PATTERN = re.compile(r"\b(\d+)\b")


class GeneticEngine:
    def evolve(self, seeds: list[AlphaCandidate], count: int) -> list[AlphaCandidate]:
        evolved: list[AlphaCandidate] = []
        for seed in islice(seeds, count):
            expression = NUMBER_PATTERN.sub(self._mutate_number, seed.expression, count=1)
            if expression == seed.expression:
                expression = f"rank(({seed.expression}) * -1)"
            evolved.append(
                AlphaCandidate(
                    expression=expression,
                    source="genetic",
                    strategy_type=seed.strategy_type,
                    rationale=f"Mutated from seed: {seed.expression}",
                    metadata={
                        **seed.metadata,
                        "generation_source": "genetic_engine",
                        "origin_agent": seed.metadata.get("origin_agent") or seed.source,
                        "parent": seed.expression,
                    },
                )
            )
        return evolved

    @staticmethod
    def _mutate_number(match: re.Match[str]) -> str:
        value = int(match.group(1))
        return str(max(2, value + 5))
