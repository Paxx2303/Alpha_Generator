from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import logging
import os
from pathlib import Path
import time
from typing import Any
import uuid

from pipeline.models import AlphaCandidate, SimulationMetrics

from .rate_limiter import RateLimiter
from .session_manager import WQSessionManager


LOGGER = logging.getLogger(__name__)
ALLOWED_SIMULATION_SETTINGS = {
    "instrumentType",
    "language",
    "unitHandling",
    "visualization",
    "delay",
    "universe",
    "truncation",
    "region",
    "decay",
    "neutralization",
    "pasteurization",
    "nanHandling",
}
SIMULATION_POLL_ATTEMPTS = 60
SIMULATION_POLL_SECONDS = 5
ALPHA_DETAILS_POLL_ATTEMPTS = 18
ALPHA_DETAILS_POLL_SECONDS = 5
SUBMISSION_POLL_ATTEMPTS = 24
SUBMISSION_POLL_SECONDS = 5
IS_PERIOD_MISMATCH_FRAGMENT = "doesn't match the current is period"
DEFAULT_SUB_UNIVERSE_CUTOFF = 0.7
SIMULATION_QUEUE_POLL_SECONDS = 1.0
SIMULATION_QUEUE_STALE_SECONDS = 60 * 60 * 2


class WorldQuantClient:
    def __init__(
        self,
        session_manager: WQSessionManager,
        rate_limiter: RateLimiter,
        base_url: str,
        queue_dir: str | Path | None = None,
    ) -> None:
        self.session_manager = session_manager
        self.rate_limiter = rate_limiter
        self.base_url = base_url.rstrip("/")
        default_queue_dir = Path(__file__).resolve().parents[1] / "runtime" / "simulation_fifo"
        self.queue_dir = Path(queue_dir) if queue_dir is not None else default_queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.queue_lock_path = self.queue_dir / "active.lock"

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        raw_response = kwargs.pop("_raw_response", False)
        self.rate_limiter.wait()
        session = self.session_manager.ensure_session()
        url = endpoint if endpoint.startswith("http://") or endpoint.startswith("https://") else f"{self.base_url}/{endpoint.lstrip('/')}"
        response = session.request(
            method=method,
            url=url,
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        if raw_response:
            return response
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text

    def list_leaderboard(self) -> list[dict[str, Any]]:
        payload = self._request(
            "GET",
            "users/self/alphas?limit=5&offset=0&order=-dateCreated&hidden=false",
        )
        return list(payload.get("results", []))

    def simulate_expression(self, candidate: AlphaCandidate) -> SimulationMetrics:
        with self._simulation_slot(candidate):
            alpha_details = self._simulate_live_alpha(candidate)
        checks = {item["name"]: item for item in alpha_details.get("is", {}).get("checks", [])}

        sharpe = float(alpha_details.get("is", {}).get("sharpe", 0.0))
        fitness = float(alpha_details.get("is", {}).get("fitness", 0.0))
        annual_returns = float(alpha_details.get("is", {}).get("returns", 0.0) or 0.0)
        turnover_raw = float(alpha_details.get("is", {}).get("turnover", 0.0) or 0.0)
        turnover = turnover_raw / 100 if turnover_raw > 1 else turnover_raw
        drawdown = float(alpha_details.get("is", {}).get("drawdown", 0.0) or 0.0)
        self_corr = float(checks.get("SELF_CORRELATION", {}).get("value", 0.0) or 0.0)
        notes = self._build_notes(alpha_details)
        return SimulationMetrics(
            sharpe=sharpe,
            fitness=fitness,
            annual_returns=annual_returns,
            turnover=turnover,
            drawdown=drawdown,
            self_correlation=self_corr,
            notes=notes,
            checks=alpha_details.get("is", {}).get("checks", []),
        )

    @contextmanager
    def _simulation_slot(self, candidate: AlphaCandidate):
        ticket = self._enqueue_simulation(candidate)
        acquired = False
        try:
            while True:
                self._cleanup_stale_queue_entries()
                if self._is_ticket_turn(ticket) and self._try_acquire_queue_lock(ticket, candidate.expression):
                    acquired = True
                    break
                time.sleep(SIMULATION_QUEUE_POLL_SECONDS)
            yield
        finally:
            # Always remove the ticket so a failed/aborted simulation does not
            # block the FIFO queue indefinitely for subsequent runs.
            try:
                ticket.unlink(missing_ok=True)
            except OSError:
                LOGGER.warning("Failed to remove simulation queue ticket %s.", ticket)
            if acquired:
                self._release_queue_lock()

    def _enqueue_simulation(self, candidate: AlphaCandidate) -> Path:
        stamp = f"{time.time_ns():020d}"
        slug = hashlib.md5(candidate.expression.encode("utf-8")).hexdigest()[:8]
        ticket = self.queue_dir / f"{stamp}_{slug}_{uuid.uuid4().hex}.ticket"
        ticket.write_text(candidate.expression, encoding="utf-8")
        LOGGER.info("Queued simulation ticket %s for expression=%s", ticket.name, candidate.expression)
        return ticket

    def _is_ticket_turn(self, ticket: Path) -> bool:
        tickets = sorted(self.queue_dir.glob("*.ticket"), key=lambda path: path.name)
        if not tickets:
            return True
        return tickets[0].name == ticket.name

    def _try_acquire_queue_lock(self, ticket: Path, expression: str) -> bool:
        try:
            fd = os.open(self.queue_lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        try:
            payload = {
                "ticket": ticket.name,
                "expression": expression,
                "acquired_at": time.time(),
            }
            os.write(fd, json.dumps(payload).encode("utf-8"))
        finally:
            os.close(fd)
        LOGGER.info("Acquired simulation FIFO lock for ticket %s", ticket.name)
        return True

    def _release_queue_lock(self) -> None:
        try:
            self.queue_lock_path.unlink(missing_ok=True)
        except OSError:
            LOGGER.warning("Failed to release simulation FIFO lock at %s", self.queue_lock_path)

    def _cleanup_stale_queue_entries(self) -> None:
        now = time.time()
        try:
            if self.queue_lock_path.exists():
                age_seconds = max(0.0, now - self.queue_lock_path.stat().st_mtime)
                if age_seconds > SIMULATION_QUEUE_STALE_SECONDS:
                    LOGGER.warning("Removing stale simulation FIFO lock older than %ss.", SIMULATION_QUEUE_STALE_SECONDS)
                    self.queue_lock_path.unlink(missing_ok=True)
            for ticket in self.queue_dir.glob("*.ticket"):
                age_seconds = max(0.0, now - ticket.stat().st_mtime)
                if age_seconds > SIMULATION_QUEUE_STALE_SECONDS:
                    LOGGER.warning("Removing stale simulation queue ticket %s.", ticket.name)
                    ticket.unlink(missing_ok=True)
        except OSError:
            LOGGER.warning("Simulation FIFO cleanup encountered a filesystem error.", exc_info=True)

    def submit_alpha(self, candidate: AlphaCandidate) -> dict[str, Any]:

        if not candidate.alpha_id:
            raise ValueError("Alpha must be simulated successfully before submission.")
        self._request("POST", f"alphas/{candidate.alpha_id}/submit")
        response = self._poll_submission(candidate.alpha_id)
        return {
            "alpha_id": candidate.alpha_id,
            "status": "submitted_check_received" if not self._checks_pending(response.get("is", {}).get("checks", [])) else "pending",
            "checks": self._normalize_checks(response.get("is", {}).get("checks", [])),
            "notes": self._build_notes(response),
        }

    def _start_simulation(self, candidate: AlphaCandidate) -> dict[str, Any]:
        settings = {
            "instrumentType": "EQUITY",
            "language": "FASTEXPR",
            "unitHandling": "VERIFY",
            "visualization": False,
            "delay": 1,
            "universe": "TOP3000",
            "truncation": 0.08,
            "region": "USA",
            "decay": 6,
            "neutralization": "SUBINDUSTRY",
            "pasteurization": "ON",
            "nanHandling": "OFF",
        }
        metadata_settings = {
            key: value
            for key, value in deepcopy(candidate.metadata).items()
            if key in ALLOWED_SIMULATION_SETTINGS
        }
        settings.update(metadata_settings)
        response = self._request(
            "POST",
            "simulations",
            _raw_response=True,
            json={
                "regular": candidate.expression,
                "type": "REGULAR",
                "settings": settings,
            },
        )
        location = response.headers.get("Location")
        if not location:
            raise RuntimeError(f"Simulation start missing Location header: {response.text[:500]}")

        for _ in range(SIMULATION_POLL_ATTEMPTS):
            payload = self._request("GET", location)
            if isinstance(payload, dict) and "alpha" in payload:
                return payload
            if isinstance(payload, dict) and payload.get("status") == "ERROR":
                raise RuntimeError(f"Simulation failed: {payload}")
            time.sleep(SIMULATION_POLL_SECONDS)

        raise TimeoutError("Timed out waiting for simulation to finish.")

    def _simulate_live_alpha(self, candidate: AlphaCandidate) -> dict[str, Any]:
        payload = self._start_simulation(candidate)
        alpha_id = str(payload["alpha"])
        candidate.alpha_id = alpha_id
        return self._wait_for_alpha_details(candidate, alpha_id=alpha_id, allow_resimulate=True)

    def _wait_for_alpha_details(
        self,
        candidate: AlphaCandidate,
        *,
        alpha_id: str,
        allow_resimulate: bool,
    ) -> dict[str, Any]:
        latest_payload: dict[str, Any] | None = None
        for _ in range(ALPHA_DETAILS_POLL_ATTEMPTS):
            alpha_details = self._request("GET", f"alphas/{alpha_id}")
            if not isinstance(alpha_details, dict):
                time.sleep(ALPHA_DETAILS_POLL_SECONDS)
                continue
            latest_payload = alpha_details
            checks = self._normalize_checks(alpha_details.get("is", {}).get("checks", []))
            alpha_details.setdefault("is", {})["checks"] = checks
            if self._needs_resimulation(alpha_details):
                if not allow_resimulate:
                    raise RuntimeError(self._build_notes(alpha_details) or "Simulation IS period mismatch persisted after retry.")
                LOGGER.warning("Alpha %s does not match current IS period; re-simulating from expression.", alpha_id)
                return self._simulate_live_alpha_resubmitted(candidate)
            if self._checks_pending(checks):
                time.sleep(ALPHA_DETAILS_POLL_SECONDS)
                continue
            return alpha_details

        if latest_payload is None:
            raise TimeoutError(f"Timed out loading alpha details for {alpha_id}.")
        # If core IS metrics are already populated, return the payload even if some
        # checks (e.g. SELF_CORRELATION) are still PENDING. The simulation itself
        # has already completed on WorldQuant Brain and the alpha is visible on the
        # web UI; only the post-simulation correlation check is lagging.
        is_block = latest_payload.get("is") or {}
        has_core_metrics = (
            is_block.get("sharpe") is not None
            and is_block.get("fitness") is not None
            and is_block.get("turnover") is not None
        )
        if has_core_metrics:
            LOGGER.warning(
                "Alpha %s checks still pending but core IS metrics are available; returning partial result.",
                alpha_id,
            )
            return latest_payload
        notes = self._build_notes(latest_payload)
        if notes:
            raise TimeoutError(f"Timed out waiting for alpha checks to settle for {alpha_id}: {notes}")
        raise TimeoutError(f"Timed out waiting for alpha checks to settle for {alpha_id}.")

    def _simulate_live_alpha_resubmitted(self, candidate: AlphaCandidate) -> dict[str, Any]:
        payload = self._start_simulation(candidate)
        alpha_id = str(payload["alpha"])
        candidate.alpha_id = alpha_id
        return self._wait_for_alpha_details(candidate, alpha_id=alpha_id, allow_resimulate=False)

    def _poll_submission(self, alpha_id: str) -> dict[str, Any]:
        latest_payload: dict[str, Any] | None = None
        for _ in range(SUBMISSION_POLL_ATTEMPTS):
            response = self._request("GET", f"alphas/{alpha_id}/submit")
            if isinstance(response, dict):
                latest_payload = response
                checks = self._normalize_checks(response.get("is", {}).get("checks", []))
                response.setdefault("is", {})["checks"] = checks
                if not self._checks_pending(checks):
                    return response
            time.sleep(SUBMISSION_POLL_SECONDS)
        if latest_payload is not None:
            return latest_payload
        raise TimeoutError(f"Timed out polling submission checks for alpha {alpha_id}.")

    @staticmethod
    def _checks_pending(checks: list[dict[str, Any]]) -> bool:
        return any(str(check.get("result", "")).upper() == "PENDING" for check in checks)

    def _needs_resimulation(self, alpha_details: dict[str, Any]) -> bool:
        message = str(alpha_details.get("message", "") or "").lower()
        return IS_PERIOD_MISMATCH_FRAGMENT in message

    def _normalize_checks(self, checks: list[dict[str, Any]] | Any) -> list[dict[str, Any]]:
        if not isinstance(checks, list):
            return []
        normalized: list[dict[str, Any]] = []
        for raw_check in checks:
            if not isinstance(raw_check, dict):
                continue
            check = dict(raw_check)
            check.setdefault("name", "UNKNOWN")
            check.setdefault("result", "UNKNOWN")
            message = str(check.get("message", "") or "").strip()
            name = str(check.get("name", "") or "")
            value = check.get("value")
            limit = check.get("limit")
            cutoff = check.get("cutoff")
            if not message and name == "LOW_SUB_UNIVERSE_SHARPE":
                actual = self._safe_float(value)
                threshold = self._safe_float(limit if limit is not None else cutoff)
                if threshold is None:
                    threshold = DEFAULT_SUB_UNIVERSE_CUTOFF
                if actual is not None:
                    message = f"Sub-universe Sharpe of {actual:.2f} is below cutoff of {threshold:.1f}."
                else:
                    message = f"Sub-universe Sharpe is below cutoff of {threshold:.1f}."
            check["message"] = message
            normalized.append(check)
        return normalized

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _build_notes(self, payload: dict[str, Any]) -> str:
        notes: list[str] = []
        message = str(payload.get("message", "") or "").strip()
        if message:
            notes.append(message)
        checks = self._normalize_checks(payload.get("is", {}).get("checks", []))
        for check in checks:
            result = str(check.get("result", "") or "").upper()
            if result in {"FAIL", "ERROR", "PENDING"}:
                detail = str(check.get("message", "") or "").strip()
                if detail:
                    notes.append(detail)
                elif result == "PENDING":
                    notes.append(f"{check.get('name')} is still pending.")
        unique_notes: list[str] = []
        seen: set[str] = set()
        for note in notes:
            key = note.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            unique_notes.append(key)
        return " ".join(unique_notes)
