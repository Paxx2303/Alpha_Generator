from __future__ import annotations

from typing import Any

from pipeline.models import SimulationMetrics


class QualityGate:
    def __init__(self, thresholds: dict[str, float]) -> None:
        self.thresholds = thresholds

    def assess(self, metrics: SimulationMetrics) -> dict[str, list[dict[str, Any]]]:
        failures: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        for check in metrics.checks:
            name = str(check.get("name", "UNKNOWN") or "UNKNOWN")
            result = str(check.get("result", "")).upper()
            detail = str(check.get("message", "") or "").strip()
            message = detail or f"WQ check {name} returned {result or 'UNKNOWN'}."
            if result in {"FAIL", "ERROR"}:
                failures.append(
                    self._issue(
                        reason=f"wq_check_{name.lower()}",
                        message=message,
                        field=name.lower(),
                        value=check.get("value"),
                        threshold=check.get("limit") if check.get("limit") is not None else check.get("cutoff"),
                    )
                )
            elif result in {"PENDING", "WARN", "WARNING"}:
                warnings.append(
                    self._issue(
                        reason=f"wq_check_{name.lower()}_warning",
                        message=message if result != "PENDING" else f"WQ check pending: {message}",
                        field=name.lower(),
                        value=check.get("value"),
                        threshold=check.get("limit") if check.get("limit") is not None else check.get("cutoff"),
                    )
                )

        self._append_threshold_failures(metrics, failures)
        self._append_threshold_warnings(metrics, warnings)
        return {"failures": self._dedupe_issues(failures), "warnings": self._dedupe_issues(warnings)}

    def evaluate(self, metrics: SimulationMetrics) -> list[str]:
        return [issue["message"] for issue in self.assess(metrics)["failures"]]

    def _append_threshold_failures(self, metrics: SimulationMetrics, failures: list[dict[str, Any]]) -> None:
        if metrics.sharpe < self.thresholds["sharpe_min"]:
            failures.append(
                self._issue(
                    reason="sharpe_below_threshold",
                    message=f"Sharpe ratio {metrics.sharpe:.2f} < threshold {self.thresholds['sharpe_min']:.2f}.",
                    field="sharpe_ratio",
                    value=metrics.sharpe,
                    threshold=self.thresholds["sharpe_min"],
                )
            )
        if metrics.fitness < self.thresholds["fitness_min"]:
            failures.append(
                self._issue(
                    reason="fitness_below_threshold",
                    message=f"Fitness {metrics.fitness:.2f} < threshold {self.thresholds['fitness_min']:.2f}.",
                    field="fitness",
                    value=metrics.fitness,
                    threshold=self.thresholds["fitness_min"],
                )
            )
        if metrics.annual_returns < self.thresholds["returns_min"]:
            failures.append(
                self._issue(
                    reason="returns_below_threshold",
                    message=f"Annual returns {metrics.annual_returns:.2f} < threshold {self.thresholds['returns_min']:.2f}.",
                    field="annual_returns",
                    value=metrics.annual_returns,
                    threshold=self.thresholds["returns_min"],
                )
            )
        sub_universe_min = self.thresholds.get("sub_universe_sharpe_min")
        if sub_universe_min is not None:
            for check in metrics.checks:
                if str(check.get("name", "")).upper() != "LOW_SUB_UNIVERSE_SHARPE":
                    continue
                value = self._safe_float(check.get("value"))
                if value is not None and value < sub_universe_min:
                    failures.append(
                        self._issue(
                            reason="sub_universe_sharpe_below_threshold",
                            message=f"Sub-universe Sharpe of {value:.2f} is below cutoff of {float(sub_universe_min):.1f}.",
                            field="sub_universe_sharpe",
                            value=value,
                            threshold=float(sub_universe_min),
                        )
                    )
                    break
        if metrics.turnover < self.thresholds["turnover_min"]:
            failures.append(
                self._issue(
                    reason="turnover_below_threshold",
                    message=f"Turnover {metrics.turnover:.2%} < minimum {self.thresholds['turnover_min']:.2%}.",
                    field="turnover",
                    value=metrics.turnover,
                    threshold=self.thresholds["turnover_min"],
                )
            )
        if metrics.turnover > self.thresholds["turnover_max"]:
            failures.append(
                self._issue(
                    reason="turnover_above_threshold",
                    message=f"Turnover {metrics.turnover:.2%} > maximum {self.thresholds['turnover_max']:.2%}.",
                    field="turnover",
                    value=metrics.turnover,
                    threshold=self.thresholds["turnover_max"],
                )
            )
        if metrics.drawdown > self.thresholds["drawdown_max"]:
            failures.append(
                self._issue(
                    reason="drawdown_above_threshold",
                    message=f"Drawdown {metrics.drawdown:.2%} > maximum {self.thresholds['drawdown_max']:.2%}.",
                    field="drawdown",
                    value=metrics.drawdown,
                    threshold=self.thresholds["drawdown_max"],
                )
            )
        if metrics.self_correlation > self.thresholds["self_correlation_max"]:
            failures.append(
                self._issue(
                    reason="self_correlation_above_threshold",
                    message=f"Self-correlation {metrics.self_correlation:.2f} > maximum {self.thresholds['self_correlation_max']:.2f}.",
                    field="self_correlation",
                    value=metrics.self_correlation,
                    threshold=self.thresholds["self_correlation_max"],
                )
            )

    def _append_threshold_warnings(self, metrics: SimulationMetrics, warnings: list[dict[str, Any]]) -> None:
        borderline = {
            "sharpe_ratio": (metrics.sharpe, self.thresholds["sharpe_min"], "min", 0.15),
            "fitness": (metrics.fitness, self.thresholds["fitness_min"], "min", 0.15),
            "annual_returns": (metrics.annual_returns, self.thresholds["returns_min"], "min", 0.02),
            "turnover_min": (metrics.turnover, self.thresholds["turnover_min"], "min", 0.02),
            "turnover_max": (metrics.turnover, self.thresholds["turnover_max"], "max", 0.05),
            "drawdown": (metrics.drawdown, self.thresholds["drawdown_max"], "max", 0.03),
            "self_correlation": (metrics.self_correlation, self.thresholds["self_correlation_max"], "max", 0.05),
        }
        for field, (value, threshold, mode, margin) in borderline.items():
            if mode == "min" and value >= threshold and value < threshold + margin:
                warnings.append(
                    self._issue(
                        reason=f"{field}_borderline",
                        message=f"{field.replace('_', ' ').title()} is borderline at {value:.2f} near threshold {threshold:.2f}.",
                        field=field,
                        value=value,
                        threshold=threshold,
                    )
                )
            if mode == "max" and value <= threshold and value > threshold - margin:
                warnings.append(
                    self._issue(
                        reason=f"{field}_borderline",
                        message=f"{field.replace('_', ' ').title()} is borderline at {value:.2f} near threshold {threshold:.2f}.",
                        field=field,
                        value=value,
                        threshold=threshold,
                    )
                )

    @staticmethod
    def _issue(
        *,
        reason: str,
        message: str,
        field: str,
        value: Any,
        threshold: Any,
    ) -> dict[str, Any]:
        return {
            "reason": reason,
            "message": message,
            "field": field,
            "value": value,
            "threshold": threshold,
        }

    @staticmethod
    def _dedupe_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for issue in issues:
            key = str(issue.get("reason") or issue.get("message") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(issue)
        return deduped

    @staticmethod
    def _safe_float(value: object) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None
