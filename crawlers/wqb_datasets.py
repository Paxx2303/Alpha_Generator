# crawlers/wqb_datasets.py — Crawl /data-sets for all configured combinations.
import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import (
    CRAWL_REGIONS, CRAWL_UNIVERSES, CRAWL_DELAYS,
    CRAWL_INSTRUMENTS, CRAWL_PAGE_LIMIT,
)
from storage.store import Store
from .base import BaseCrawler


class WQBDatasetCrawler(BaseCrawler):
    """Crawl all datasets across the configured region × universe × delay matrix."""

    key = "wqb_datasets"
    BASE = "https://api.worldquantbrain.com/data-sets"

    def pages(self, resume_cursor=None):
        # cursor = {"region":, "universe":, "delay":, "instrument":, "offset":}
        # Build the full list of (region, universe, delay, instrument) combos to iterate
        combos = [
            (r, u, d, i)
            for r in CRAWL_REGIONS
            for u in CRAWL_UNIVERSES
            for d in CRAWL_DELAYS
            for i in CRAWL_INSTRUMENTS
        ]

        start_combo_idx = 0
        start_offset = 0
        if resume_cursor:
            key = (resume_cursor["region"], resume_cursor["universe"],
                   resume_cursor["delay"], resume_cursor["instrument"])
            if key in [(c[0], c[1], c[2], c[3]) for c in combos]:
                start_combo_idx = [
                    (c[0], c[1], c[2], c[3]) for c in combos
                ].index(key)
                start_offset = resume_cursor.get("offset", 0)

        for idx, (region, universe, delay, instrument) in enumerate(combos):
            if idx < start_combo_idx:
                continue
            offset = start_offset if idx == start_combo_idx else 0

            while True:
                url = (
                    f"{self.BASE}?delay={delay}&instrumentType={instrument}"
                    f"&region={region}&universe={universe}"
                    f"&limit={CRAWL_PAGE_LIMIT}&offset={offset}"
                )
                res = self.get(url)
                if res.status_code != 200:
                    break

                data = res.json()
                results = data.get("results", [])
                if not results:
                    break

                # Tag rows with crawl context so Store knows how to store them
                for row in results:
                    row["_region"] = region
                    row["_universe"] = universe
                    row["_delay"] = delay
                    row["_instrument_type"] = instrument

                cursor = {
                    "region": region, "universe": universe,
                    "delay": delay, "instrument": instrument,
                    "offset": offset + len(results),
                }
                yield cursor, results

                if len(results) < CRAWL_PAGE_LIMIT:
                    break
                offset += CRAWL_PAGE_LIMIT

    def persist(self, rows: list) -> int:
        return self.store.upsert_datasets(rows)
