"""
Source Intelligence — track which knowledge sources generate gold alphas.
Backed by the knowledge_sources table in alpha_store.db.
"""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from storage.store import Store

VALID_DOMAINS = {"general_quant", "wqb_specific"}
VALID_TYPES = {
    "arxiv", "ssrn", "quant_blog", "book", "research_report",
    "wqb_forum", "wqb_docs", "brain_tips", "manual",
}


class SourceRegistry:
    def __init__(self, store: Store | None = None):
        self._store = store or Store()

    def _sid(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def register(
        self,
        url: str,
        source_domain: str,
        source_type: str,
        title: str = "",
        notes: str = "",
    ) -> str:
        """Register a new knowledge source. Returns source_id."""
        assert source_domain in VALID_DOMAINS, f"Invalid domain: {source_domain}"
        assert source_type in VALID_TYPES,     f"Invalid type: {source_type}"
        sid = self._sid(url)
        self._store.register_source(sid, url, source_domain, source_type, title, notes)
        return sid

    def record_alpha(self, source_id: str, status: str) -> None:
        """
        Record an alpha result for a source.
        status: 'gold' | 'failed' | 'correlated'
        """
        assert status in {"gold", "failed", "correlated"}
        self._store.record_source_alpha(source_id, status)

    def effectiveness(self, source_id: str) -> float:
        """Return effectiveness ratio for a single source (0.0–1.0)."""
        row = self._store.get_source(source_id)
        if not row:
            return 0.0
        tested = row.get("alphas_tested", 0)
        gold   = row.get("alphas_gold", 0)
        return gold / tested if tested > 0 else 0.0

    def domain_stats(self) -> list[dict]:
        """Aggregate effectiveness by source_domain (TỔNG level)."""
        return self._store.source_domain_stats()

    def type_stats(self) -> list[dict]:
        """Aggregate effectiveness by source_domain + source_type."""
        return self._store.source_type_stats()

    def priority_sources(self, top_n: int = 5, domain: str | None = None) -> list[dict]:
        """Return top-n sources by effectiveness, optionally filtered by domain."""
        return self._store.priority_sources(top_n=top_n, domain=domain)

    def should_revisit(self, source_id: str) -> bool:
        """True if source has high effectiveness but hasn't been checked recently (> 7 days)."""
        from datetime import datetime, timedelta, UTC
        row = self._store.get_source(source_id)
        if not row or row.get("is_blacklisted"):
            return False
        eff = self.effectiveness(source_id)
        if eff < 0.1:
            return False
        last = row.get("last_checked")
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
            return (datetime.now(UTC) - last_dt) > timedelta(days=7)
        except Exception:
            return True

    def blacklist(self, source_id: str, reason: str) -> None:
        self._store.blacklist_source(source_id, reason)

    def get_domain_weights(self) -> dict:
        """
        Return suggested crawl weight per domain based on effectiveness.
        {"general_quant": 0.4, "wqb_specific": 0.6}
        """
        stats = {r["source_domain"]: r for r in self.domain_stats()}
        total_gold = sum(s.get("total_gold", 0) for s in stats.values()) or 1
        weights = {}
        for domain in VALID_DOMAINS:
            gold = stats.get(domain, {}).get("total_gold", 0)
            weights[domain] = round(gold / total_gold, 2)
        return weights


if __name__ == "__main__":
    reg = SourceRegistry()
    # Quick smoke test
    sid = reg.register(
        "https://arxiv.org/abs/test",
        "general_quant",
        "arxiv",
        title="Test Paper",
    )
    reg.record_alpha(sid, "gold")
    reg.record_alpha(sid, "failed")
    print("Domain stats:", reg.domain_stats())
    print("Effectiveness:", reg.effectiveness(sid))
    print("Domain weights:", reg.get_domain_weights())
