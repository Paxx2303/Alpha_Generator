# crawlers/base.py — Shared base for all WQB crawlers (v2 Ingestion Layer).
#
# Pattern borrowed from worldquant-miner (concern separation) and
# q3yi/worldquant (SQLite-backed, typed crawl).
import time
from dataclasses import dataclass, field
from typing import Any, Generator

import structlog
from tenacity import (
    retry, wait_exponential, stop_after_attempt,
    retry_if_exception_type, before_sleep_log,
)

import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import CRAWL_RATE_QPS
from storage.store import Store

logger = structlog.get_logger()


@dataclass
class CrawlResult:
    fetched: int = 0
    upserted: int = 0
    skipped: int = 0
    resumed_from: Any = None
    error: str = ""

    @property
    def success(self) -> bool:
        return not self.error

    def summary(self) -> str:
        parts = [f"fetched={self.fetched}", f"upserted={self.upserted}"]
        if self.skipped:     parts.append(f"skipped={self.skipped}")
        if self.resumed_from: parts.append(f"resumed_from={self.resumed_from}")
        if self.error:        parts.append(f"ERROR={self.error}")
        return "  ".join(parts)


class BaseCrawler:
    """
    Template-method base for all WQB API crawlers.

    Subclasses implement:
        key          — unique string for crawl_state checkpointing
        pages()      — generator yielding (cursor, [raw_rows])
        persist(rows)— call store.upsert_* and return count upserted
    """

    key: str = "base"
    _min_interval: float = 1.0 / max(CRAWL_RATE_QPS, 0.1)

    def __init__(self, session, store: Store):
        self.session = session   # authenticated requests.Session from WQBClient
        self.store = store
        self._last_req: float = 0.0
        self.headers: dict = {}

    # ── Public entry point ──────────────────────────────────────────────────
    def run(self, resume: bool = True) -> CrawlResult:
        result = CrawlResult()
        state = self.store.get_crawl_state(self.key) if resume else None
        if state:
            result.resumed_from = state
            logger.info("crawler.resume", key=self.key, cursor=state)
        else:
            logger.info("crawler.start", key=self.key)

        try:
            for cursor, rows in self.pages(resume_cursor=state):
                result.fetched += len(rows)
                result.upserted += self.persist(rows)
                self.store.set_crawl_state(self.key, cursor)
                logger.info("crawler.page", key=self.key, cursor=cursor,
                            fetched=len(rows), total=result.fetched)
        except Exception as exc:
            result.error = str(exc)
            logger.error("crawler.error", key=self.key, error=str(exc))
            return result

        self.store.clear_crawl_state(self.key)
        logger.info("crawler.done", key=self.key, **{"fetched": result.fetched,
                                                      "upserted": result.upserted})
        return result

    # ── Subclass interface ──────────────────────────────────────────────────
    def pages(self, resume_cursor=None) -> Generator:
        raise NotImplementedError

    def persist(self, rows: list) -> int:
        raise NotImplementedError

    # ── HTTP helper with rate-limit + retry ─────────────────────────────────
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def get(self, url: str) -> dict:
        elapsed = time.time() - self._last_req
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        t0 = time.time()
        res = self.session.get(url, headers=self.headers)
        latency_ms = int((time.time() - t0) * 1000)
        self._last_req = time.time()

        if res.status_code == 429:
            retry_after = int(res.headers.get("Retry-After", 15))
            logger.warning("crawler.rate_limited", url=url, retry_after=retry_after)
            time.sleep(retry_after)
            raise Exception("Rate limited — retrying")

        if res.status_code >= 500:
            logger.warning("crawler.server_error", url=url, status=res.status_code)
            raise Exception(f"Server error {res.status_code}")

        logger.debug("crawler.request", url=url, status=res.status_code, latency_ms=latency_ms)
        return res
