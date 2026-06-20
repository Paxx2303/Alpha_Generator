# crawlers/wqb_operators.py — Crawl /operators from WQB API.
#
# Operators stored in the `operators` table power expression validation
# (see design.md §3.7 and §8 — Qlib-style operator registry).
import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from storage.store import Store
from .base import BaseCrawler


class WQBOperatorCrawler(BaseCrawler):
    """Crawl all operators and cache locally for offline expression validation."""

    key = "wqb_operators"
    BASE = "https://api.worldquantbrain.com/operators"

    def pages(self, resume_cursor=None):
        # WQB operators endpoint typically returns all at once (no paging needed)
        res = self.get(self.BASE)
        if res.status_code != 200:
            return

        data = res.json()
        # Response may be a list or {"results": [...]}
        if isinstance(data, list):
            operators = data
        else:
            operators = data.get("results", data.get("operators", []))

        if operators:
            yield {"done": True}, operators

    def persist(self, rows: list) -> int:
        return self.store.upsert_operators(rows)
