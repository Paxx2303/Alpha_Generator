from __future__ import annotations

from datetime import datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path
import logging
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


LOGGER = logging.getLogger(__name__)


class DailyResearcher:
    def __init__(self, root: str | Path, config: dict) -> None:
        self.root = Path(root)
        self.config = config
        self.failure_root = self.root / "failure_recovery"
        self.root.mkdir(parents=True, exist_ok=True)
        self.failure_root.mkdir(parents=True, exist_ok=True)

    def refresh(self) -> str:
        stamp = datetime.now().strftime("%Y-%m-%d")
        out_path = self.root / f"{stamp}.md"
        if out_path.exists():
            return out_path.read_text(encoding="utf-8")
        sections: list[str] = [f"# Daily Research Digest - {stamp}", ""]

        rss_feeds = self.config.get("rss_feeds", [])
        for feed in rss_feeds:
            entries = self._fetch_rss(feed, limit=5)
            if entries:
                sections.append(f"## RSS Feed: {feed}")
                sections.extend(f"- {item}" for item in entries)
                sections.append("")

        arxiv_queries = self.config.get("arxiv_queries", [])
        for query in arxiv_queries:
            entries = self._fetch_arxiv(query, limit=3)
            if entries:
                sections.append(f"## arXiv: {query}")
                sections.extend(f"- {item}" for item in entries)
                sections.append("")

        content = "\n".join(sections).strip() + "\n"
        out_path.write_text(content, encoding="utf-8")
        LOGGER.info("Daily research digest written to %s", out_path)
        return content

    def targeted_research(self, topics: list[str], tag: str) -> str:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_tag = "".join(char.lower() if char.isalnum() else "-" for char in tag).strip("-") or "recovery"
        out_path = self.failure_root / f"{stamp}_{safe_tag}.md"

        sections: list[str] = [
            f"# Failure Recovery Research - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        for topic in topics:
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(topic)}"
            rss_entries = self._fetch_rss(rss_url, limit=3)
            if rss_entries:
                sections.append(f"## Market Research: {topic}")
                sections.extend(f"- {item}" for item in rss_entries)
                sections.append("")

            arxiv_entries = self._fetch_arxiv(topic, limit=1)
            if arxiv_entries:
                sections.append(f"## Paper Search: {topic}")
                sections.extend(f"- {item}" for item in arxiv_entries)
                sections.append("")

        content = "\n".join(sections).strip() + "\n"
        out_path.write_text(content, encoding="utf-8")
        LOGGER.info("Failure recovery research written to %s", out_path)
        return content

    def _fetch_rss(self, url: str, limit: int = 5) -> list[str]:
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                raw = response.read()
        except Exception as exc:
            LOGGER.warning("RSS fetch failed for %s: %s", url, exc)
            return []

        try:
            feed = BytesParser(policy=policy.default).parsebytes(raw)
            payload = feed.get_payload(decode=True) if feed.is_multipart() else raw
            root = ET.fromstring(payload)
        except Exception:
            try:
                root = ET.fromstring(raw)
            except Exception as exc:
                LOGGER.warning("RSS parse failed for %s: %s", url, exc)
                return []

        items = []
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            if title:
                items.append(f"{title} | {link}")
        return items

    def _fetch_arxiv(self, query: str, limit: int = 3) -> list[str]:
        encoded = urllib.parse.quote(query)
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{encoded}&start=0&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
        )
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                raw = response.read()
            root = ET.fromstring(raw)
        except Exception as exc:
            LOGGER.warning("arXiv fetch failed for %s: %s", query, exc)
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items: list[str] = []
        for entry in root.findall("atom:entry", ns)[:limit]:
            title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
            link = ""
            for node in entry.findall("atom:link", ns):
                if node.attrib.get("title") == "pdf":
                    link = node.attrib.get("href", "")
                    break
            summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
            summary = textwrap.shorten(summary, width=180, placeholder="...")
            if title:
                items.append(f"{title} | {summary} | {link}")
        return items
