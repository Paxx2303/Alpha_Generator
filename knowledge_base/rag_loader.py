from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from database import AlphaStore
from pypdf import PdfReader


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(slots=True)
class DocumentChunk:
    text: str
    source: str


class WQKnowledgeBase:
    def __init__(self, root: str | Path, theory_store: AlphaStore | None = None) -> None:
        self.root = Path(root)
        self.theory_store = theory_store
        self.documents: list[DocumentChunk] = []

    def load_all(self) -> None:
        self.documents.clear()
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in {".md", ".txt", ".json", ".html"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
            elif path.suffix.lower() == ".pdf":
                text = self._extract_pdf_text(path)
            else:
                continue
            self.documents.extend(self._split_text(text, source=str(path.relative_to(self.root))))
        self._load_theory_documents()

    def _load_theory_documents(self) -> None:
        if self.theory_store is None:
            return
        for row in self.theory_store.list_theory_entries(limit=500):
            text = self._theory_row_to_text(row)
            self.documents.extend(self._split_text(text, source=f"db:theory:{row['theory_id']}"))

    @staticmethod
    def _theory_row_to_text(row: dict[str, object]) -> str:
        import json

        def parse_list(value: object) -> list[str]:
            if isinstance(value, list):
                return [str(item) for item in value]
            try:
                raw = json.loads(str(value))
            except json.JSONDecodeError:
                return []
            if isinstance(raw, list):
                return [str(item) for item in raw]
            return []

        sectors = parse_list(row.get("sector_tags_json"))
        implications = parse_list(row.get("alpha_implication_json"))
        reasoning = parse_list(row.get("agent_reasoning_json"))
        lines = [
            f"Theory ID: {row.get('theory_id', '')}",
            f"Domain: {row.get('domain', '')}",
            f"Title: {row.get('title', '')}",
            f"Sectors: {', '.join(sectors)}",
            f"Core Principle: {row.get('core_principle', '')}",
            "Alpha Implication:",
            *[f"- {item}" for item in implications],
            f"Example Expression: {row.get('example_expression', '')}",
            "Agent Reasoning:",
            *[f"- {item}" for item in reasoning],
        ]
        return "\n".join(lines)

    def _extract_pdf_text(self, path: Path) -> str:
        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    def _split_text(self, text: str, source: str, chunk_size: int = 900) -> Iterable[DocumentChunk]:
        buffer: list[str] = []
        size = 0
        for line in text.splitlines():
            buffer.append(line)
            size += len(line)
            if size >= chunk_size:
                yield DocumentChunk(text="\n".join(buffer), source=source)
                buffer = []
                size = 0
        if buffer:
            yield DocumentChunk(text="\n".join(buffer), source=source)

    def query_context(self, query: str, k: int = 5) -> str:
        if not self.documents:
            self.load_all()
        query_tokens = set(TOKEN_PATTERN.findall(query.lower()))
        scored: list[tuple[int, DocumentChunk]] = []
        for doc in self.documents:
            doc_tokens = set(TOKEN_PATTERN.findall(doc.text.lower()))
            scored.append((len(query_tokens & doc_tokens), doc))
        ranked = [doc for score, doc in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0]
        if not ranked:
            ranked = self.documents[:k]
        snippets = [f"[{doc.source}]\n{doc.text.strip()}" for doc in ranked[:k]]
        return "\n\n---\n\n".join(snippets)

    def get_alpha_context(self, strategy_type: str, n: int = 5) -> str:
        return self.query_context(f"WorldQuant alpha {strategy_type} operators templates", k=n)

    def get_failure_context(self, n: int = 3) -> str:
        return self.query_context("rejection reasons sharpe turnover correlation failures", k=n)

    def get_theory_context(self, query: str, n: int = 5) -> str:
        if self.theory_store is not None:
            return self.theory_store.theory_context(query, limit=n)
        return self.query_context(query, k=n)
