from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api_layer.rate_limiter import RateLimiter
from api_layer.session_manager import WQSessionManager
from api_layer.wq_client import WorldQuantClient
from pipeline.models import AlphaCandidate
from pipeline.submission.auto_submit import AutoSubmitter
from pipeline.submission.quality_gate import QualityGate


@dataclass
class FakeResponse:
    headers: dict[str, str]
    text: str = ""


class FakeStore:
    def daily_submission_count(self, day: str | None = None) -> int:
        del day
        return 0


class ScriptedWorldQuantClient(WorldQuantClient):
    def __init__(self) -> None:
        super().__init__(
            session_manager=WQSessionManager(username="", password="", base_url="http://fake", dry_run=False),
            rate_limiter=RateLimiter(0),
            base_url="http://fake",
            dry_run=False,
        )
        self.submit_poll_count = 0
        self.alpha_new_poll_count = 0
        self.simulation_start_count = 0

    def _request(self, method: str, endpoint: str, **kwargs):  # type: ignore[override]
        raw_response = kwargs.pop("_raw_response", False)
        if method == "POST" and endpoint == "simulations" and raw_response:
            self.simulation_start_count += 1
            if self.simulation_start_count == 1:
                return FakeResponse(headers={"Location": "simulations/old"})
            return FakeResponse(headers={"Location": "simulations/new"})

        if method == "GET" and endpoint == "simulations/old":
            return {"alpha": "alpha-old"}

        if method == "GET" and endpoint == "alphas/alpha-old":
            return {
                "message": "The simulation doesn't match the current IS period. Please clone this alpha and re-simulate.",
                "is": {
                    "checks": [],
                },
            }

        if method == "GET" and endpoint == "simulations/new":
            return {"alpha": "alpha-new"}

        if method == "GET" and endpoint == "alphas/alpha-new":
            self.alpha_new_poll_count += 1
            if self.alpha_new_poll_count == 1:
                return {
                    "message": "",
                    "is": {
                        "checks": [
                            {"name": "LOW_SUB_UNIVERSE_SHARPE", "result": "PENDING"},
                        ],
                    },
                }
            return {
                "message": "",
                "is": {
                    "sharpe": 1.81,
                    "fitness": 1.23,
                    "returns": 0.11,
                    "turnover": 21.0,
                    "drawdown": 0.14,
                    "checks": [
                        {"name": "LOW_SUB_UNIVERSE_SHARPE", "result": "FAIL", "value": 0.65, "limit": 0.7},
                        {"name": "SELF_CORRELATION", "result": "PASS", "value": 0.31},
                    ],
                },
            }

        if method == "POST" and endpoint == "alphas/alpha-new/submit":
            return {"status": "ok"}

        if method == "GET" and endpoint == "alphas/alpha-new/submit":
            self.submit_poll_count += 1
            if self.submit_poll_count == 1:
                return {
                    "message": "",
                    "is": {
                        "checks": [
                            {"name": "SUBMISSION", "result": "PENDING"},
                        ],
                    },
                }
            return {
                "message": "",
                "is": {
                    "checks": [
                        {"name": "SUBMISSION", "result": "PASS"},
                    ],
                },
            }

        raise AssertionError(f"Unexpected request: {method} {endpoint}")


def main() -> None:
    client = ScriptedWorldQuantClient()
    candidate = AlphaCandidate(
        expression="rank(ts_mean(returns, 20))",
        source="test",
        strategy_type="momentum",
        metadata={"region": "USA", "universe": "TOP3000", "neutralization": "SUBINDUSTRY"},
    )

    metrics = client.simulate_expression(candidate)
    assert candidate.alpha_id == "alpha-new", f"Expected re-simulated alpha id, got {candidate.alpha_id!r}"
    assert client.simulation_start_count == 2, f"Expected 2 simulations, got {client.simulation_start_count}"
    assert client.alpha_new_poll_count == 2, f"Expected pending + final alpha detail polls, got {client.alpha_new_poll_count}"
    assert metrics.checks[0]["message"] == "Sub-universe Sharpe of 0.65 is below cutoff of 0.7."
    assert "Sub-universe Sharpe of 0.65 is below cutoff of 0.7." in metrics.notes

    gate = QualityGate(
        {
            "sharpe_min": 1.5,
            "fitness_min": 1.0,
            "returns_min": 0.05,
            "sub_universe_sharpe_min": 0.70,
            "turnover_min": 0.01,
            "turnover_max": 0.70,
            "drawdown_max": 0.30,
            "self_correlation_max": 0.70,
        }
    )
    reasons = gate.evaluate(metrics)
    assert reasons == ["Sub-universe Sharpe of 0.65 is below cutoff of 0.7."], reasons

    submitter = AutoSubmitter(client, FakeStore(), daily_limit=1)
    submitted, result = submitter.submit(candidate)
    assert submitted is True, result
    assert result["status"] == "submitted_check_received", result
    assert client.submit_poll_count == 2, f"Expected pending + final submit polls, got {client.submit_poll_count}"

    print("PASS: IS period mismatch retry, pending check polling, and sub-universe Sharpe handling are working.")


if __name__ == "__main__":
    main()
