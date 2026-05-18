from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any

from api_layer import WorldQuantClient
from database import AlphaStore
from pipeline.models import AlphaCandidate


LOGGER = logging.getLogger(__name__)


class AutoSubmitter:
    def __init__(self, client: WorldQuantClient, store: AlphaStore, daily_limit: int) -> None:
        self.client = client
        self.store = store
        self.daily_limit = daily_limit
        self.lock_path = self.store.db_path.parent / ".alpha_submit.lock"
        self.history_path = self.store.db_path.parent / ".alpha_submit_history.json"

    def submit(self, candidate: AlphaCandidate) -> tuple[bool, dict]:
        acquired = self._acquire_lock()
        if not acquired:
            LOGGER.warning("Another submit in progress, skipping")
            return False, {"status": "skipped", "reason": "Another submit in progress, skipping"}
        try:
            if self._already_submitted(candidate):
                LOGGER.warning("Alpha %s already submitted, skipping", candidate.expression)
                return False, {"status": "skipped", "reason": "Alpha already submitted, skipping", "already_submitted": True}
            if self.store.daily_submission_count() >= self.daily_limit:
                return False, {"status": "skipped", "reason": "Daily submission limit reached."}
            result = self.client.submit_alpha(candidate)
            submitted_at = datetime.now(timezone.utc).isoformat()
            self._record_submission(candidate, submitted_at=submitted_at, result=result)
            if result.get("status") == "pending":
                return False, {
                    "status": "pending",
                    "reason": result.get("notes", "Submission checks are still pending."),
                    "checks": result.get("checks", []),
                    "submitted_at": submitted_at,
                }
            payload = dict(result)
            payload["submitted_at"] = submitted_at
            return True, payload
        finally:
            self._release_lock()

    def _already_submitted(self, candidate: AlphaCandidate) -> bool:
        if self.store.was_expression_submitted(candidate.expression):
            return True
        history = self._load_history()
        key = self._history_key(candidate)
        return key in history or candidate.expression in history

    def _record_submission(self, candidate: AlphaCandidate, *, submitted_at: str, result: dict[str, Any]) -> None:
        history = self._load_history()
        entry = {
            "expression": candidate.expression,
            "alpha_id": candidate.alpha_id,
            "submitted_at": submitted_at,
            "status": result.get("status"),
        }
        history[self._history_key(candidate)] = entry
        history[candidate.expression] = entry
        self._save_history(history)

    def _history_key(self, candidate: AlphaCandidate) -> str:
        return candidate.alpha_id or candidate.expression

    def _load_history(self) -> dict[str, Any]:
        if not self.history_path.exists():
            return {}
        try:
            return json.loads(self.history_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_history(self, payload: dict[str, Any]) -> None:
        self.history_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _acquire_lock(self) -> bool:
        try:
            if self.lock_path.exists():
                age_seconds = max(0.0, datetime.now(timezone.utc).timestamp() - self.lock_path.stat().st_mtime)
                if age_seconds > 600:
                    self.lock_path.unlink(missing_ok=True)
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(str(os.getpid()))
            return True
        except FileExistsError:
            return False

    def _release_lock(self) -> None:
        try:
            self.lock_path.unlink(missing_ok=True)
        except OSError:
            LOGGER.warning("Failed to release submit lock at %s", self.lock_path)
