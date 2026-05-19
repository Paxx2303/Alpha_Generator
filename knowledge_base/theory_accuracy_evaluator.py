"""
Theory Accuracy Evaluator
Evaluates how well applied theories correlate with actual alpha performance metrics.
"""

from __future__ import annotations

from typing import Dict, List, Any
from collections import defaultdict


class TheoryAccuracyEvaluator:
    """
    Tracks which theories were applied to an alpha and measures their correlation
    with final performance metrics (Sharpe, Fitness, Turnover, etc.).
    """

    def __init__(self):
        # theory_name -> list of (sharpe, fitness, turnover)
        self.records: Dict[str, List[tuple[float, float, float]]] = defaultdict(list)

    def record_theory_application(
        self,
        theory_name: str,
        sharpe: float,
        fitness: float,
        turnover: float,
    ) -> None:
        """Record one instance of a theory being applied to an alpha."""
        self.records[theory_name].append((sharpe, fitness, turnover))

    def evaluate(self) -> Dict[str, Dict[str, float]]:
        """
        Compute average performance for each theory.
        Returns dict: theory_name -> {avg_sharpe, avg_fitness, avg_turnover, count}
        """
        result = {}
        for theory, values in self.records.items():
            if not values:
                continue
            sharpes = [v[0] for v in values]
            fitnesses = [v[1] for v in values]
            turnovers = [v[2] for v in values]

            result[theory] = {
                "avg_sharpe": round(sum(sharpes) / len(sharpes), 3),
                "avg_fitness": round(sum(fitnesses) / len(fitnesses), 3),
                "avg_turnover": round(sum(turnovers) / len(turnovers), 3),
                "count": len(values),
            }
        return result

    def get_best_theories(self, min_count: int = 3) -> List[str]:
        """Return theories with highest average Fitness (only those with enough samples)."""
        evaluated = self.evaluate()
        filtered = {
            k: v for k, v in evaluated.items() if v["count"] >= min_count
        }
        sorted_theories = sorted(
            filtered.items(), key=lambda x: x[1]["avg_fitness"], reverse=True
        )
        return [name for name, _ in sorted_theories[:5]]

    def reset(self) -> None:
        """Clear all records."""
        self.records.clear()
