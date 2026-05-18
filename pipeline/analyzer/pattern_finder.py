from __future__ import annotations

from collections import Counter
import re

from pipeline.models import AlphaCandidate


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class PatternFinder:
    def operator_frequency(self, candidates: list[AlphaCandidate], top_n: int = 10) -> list[tuple[str, int]]:
        counter: Counter[str] = Counter()
        for candidate in candidates:
            counter.update(TOKEN_PATTERN.findall(candidate.expression))
        return counter.most_common(top_n)

