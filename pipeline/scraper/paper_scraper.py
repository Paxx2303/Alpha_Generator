from __future__ import annotations

from pathlib import Path
import re

from pypdf import PdfReader


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class PaperScraper:
    def __init__(self, research_root: str | Path) -> None:
        self.research_root = Path(research_root)

    def discover_sources(self) -> list[dict[str, str]]:
        if not self.research_root.exists():
            return []
        return [
            {"path": str(path), "name": path.stem, "type": path.suffix.lower()}
            for path in self.research_root.rglob("*")
            if path.is_file() and path.suffix.lower() in {".md", ".txt", ".pdf"}
        ]

    def select_relevant(self, query: str, limit: int = 1) -> list[dict[str, str]]:
        query_tokens = set(TOKEN_PATTERN.findall(query.lower()))
        scored: list[tuple[int, dict[str, str]]] = []
        for source in self.discover_sources():
            path = Path(source["path"])
            seed_text = f"{path.stem} {path.parent.name}".lower()
            score = len(query_tokens & set(TOKEN_PATTERN.findall(seed_text)))
            scored.append((score, source))
        ranked = [source for score, source in sorted(scored, key=lambda item: item[0], reverse=True)]
        return ranked[:limit]

    def read_excerpt(self, path: str | Path, max_chars: int = 4000) -> str:
        source_path = Path(path)
        suffix = source_path.suffix.lower()
        if suffix in {".md", ".txt"}:
            text = source_path.read_text(encoding="utf-8", errors="ignore")
        elif suffix == ".pdf":
            reader = PdfReader(str(source_path))
            pages = [page.extract_text() or "" for page in reader.pages[:5]]
            text = "\n".join(pages)
        else:
            return ""
        return text[:max_chars].strip()

    def build_paper_digest(self, query: str, limit: int = 1, max_chars: int = 3000) -> list[dict[str, str]]:
        digests: list[dict[str, str]] = []
        for source in self.select_relevant(query, limit=limit):
            excerpt = self.read_excerpt(source["path"], max_chars=max_chars)
            if not excerpt:
                continue
            digests.append(
                {
                    **source,
                    "excerpt": excerpt,
                }
            )
        return digests
