from __future__ import annotations

import re

from pipeline.models import AlphaCandidate


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class CorrelationChecker:
    def estimate_self_correlation(
        self,
        candidate: AlphaCandidate,
        history: list[dict],
    ) -> float:
        if not history:
            return 0.0

        candidate_tokens = set(TOKEN_PATTERN.findall(candidate.expression))
        if not candidate_tokens:
            return 0.0

        highest = 0.0
        for item in history:
            historical_tokens = set(TOKEN_PATTERN.findall(item["expression"]))
            union = candidate_tokens | historical_tokens
            if not union:
                continue
            score = len(candidate_tokens & historical_tokens) / len(union)
            highest = max(highest, score)
        return round(highest, 3)

