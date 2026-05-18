from __future__ import annotations

from itertools import cycle, islice
from typing import Any

from pipeline.models import AlphaCandidate


class TemplateEngine:
    def __init__(self, generation_config: dict[str, Any]) -> None:
        self.generation_config = generation_config

    def generate(self, strategy_type: str, count: int) -> list[AlphaCandidate]:
        templates = self.generation_config["operators"].get(strategy_type) or self.generation_config["operators"]["momentum"]
        lookbacks = self.generation_config.get("lookbacks", [5, 10, 20])
        candidates: list[AlphaCandidate] = []
        for template, lookback in islice(zip(cycle(templates), cycle(lookbacks)), count):
            candidates.append(
                AlphaCandidate(
                    expression=template.format(lookback=lookback),
                    source="template",
                    strategy_type=strategy_type,
                    rationale=f"Template-based {strategy_type} alpha with lookback {lookback}.",
                    metadata={
                        "generation_source": "template_engine",
                        "origin_agent": "template_engine",
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
            )
        return candidates
