from __future__ import annotations

from statistics import mean

from pipeline.models import EvaluatedAlpha


class AlphaAnalyzer:
    def summarize(self, evaluated: list[EvaluatedAlpha]) -> dict[str, float]:
        if not evaluated:
            return {
                "count": 0,
                "avg_sharpe": 0.0,
                "avg_fitness": 0.0,
                "avg_turnover": 0.0,
            }
        return {
            "count": len(evaluated),
            "avg_sharpe": round(mean(item.metrics.sharpe for item in evaluated), 3),
            "avg_fitness": round(mean(item.metrics.fitness for item in evaluated), 3),
            "avg_turnover": round(mean(item.metrics.turnover for item in evaluated), 3),
        }

