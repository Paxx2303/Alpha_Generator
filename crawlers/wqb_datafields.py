# crawlers/wqb_datafields.py — Crawl /data-fields per dataset, region × universe × delay.
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


class WQBDataFieldCrawler(BaseCrawler):
    """
    Crawl data fields for every dataset stored in the datasets table.

    Adds columns: type (MATRIX/VECTOR/GROUP), coverage, user_count — these are
    critical for expression validation and field recommendations (Qlib-style catalog).
    """

    key = "wqb_datafields"
    BASE = "https://api.worldquantbrain.com/data-fields"

    def pages(self, resume_cursor=None):
        # Load all known datasets from store
        datasets = [
            dict(r) for r in self.store.conn.execute(
                "SELECT DISTINCT id, region, universe, delay FROM datasets"
            ).fetchall()
        ]

        if not datasets:
            # Fallback: iterate from config without needing datasets table
            datasets = [
                {"id": None, "region": r, "universe": u, "delay": d}
                for r in CRAWL_REGIONS
                for u in CRAWL_UNIVERSES
                for d in CRAWL_DELAYS
            ]

        skip_to = None
        if resume_cursor:
            skip_to = (
                resume_cursor.get("dataset_id"),
                resume_cursor.get("region"),
                resume_cursor.get("universe"),
                resume_cursor.get("delay"),
            )

        for ds in datasets:
            ds_id = ds["id"]
            region = ds["region"]
            universe = ds["universe"]
            delay = ds["delay"]
            combo = (ds_id, region, universe, delay)

            if skip_to:
                if combo != skip_to:
                    continue
                skip_to = None  # matched — start crawling from here

            offset = resume_cursor.get("offset", 0) if resume_cursor else 0
            resume_cursor = None  # only use offset for first matching combo

            while True:
                url = (
                    f"{self.BASE}?"
                    + (f"dataset.id={ds_id}&" if ds_id else "")
                    + f"delay={delay}&instrumentType=EQUITY"
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

                for row in results:
                    row["_region"] = region
                    row["_universe"] = universe
                    row["_delay"] = delay
                    row["_dataset_id"] = ds_id

                cursor = {
                    "dataset_id": ds_id,
                    "region": region, "universe": universe,
                    "delay": delay, "offset": offset + len(results),
                }
                yield cursor, results

                if len(results) < CRAWL_PAGE_LIMIT:
                    break
                offset += CRAWL_PAGE_LIMIT

    def persist(self, rows: list) -> int:
        return self.store.upsert_datafields(rows)
