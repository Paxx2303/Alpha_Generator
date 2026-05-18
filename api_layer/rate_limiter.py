from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time


@dataclass
class RateLimiter:
    min_interval_seconds: float = 2.0
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _last_call: float = field(default=0.0, init=False)

    def wait(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_call
            remaining = self.min_interval_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)
            self._last_call = time.monotonic()

