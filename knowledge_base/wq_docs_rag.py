"""WorldQuant Brain documentation RAG.

Wraps `WQKnowledgeBase` to expose a thin, focused API for retrieving
authoritative WorldQuant Brain documentation snippets when prompting
Hermes / DeerFlow / OpenRouter for alpha generation.

The corpus lives under `docs/wq_brain/` (see its README for how to
populate it from <https://platform.worldquantbrain.com/learn/documentation>).
"""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from .rag_loader import WQKnowledgeBase

_DEFAULT_DOCS_ROOT = Path(__file__).resolve().parent.parent / "docs" / "wq_brain"
_SECONDARY_ROOTS = [
    Path(__file__).resolve().parent / "wq_official",
]


class WQBrainDocsRAG:
    """Lazy, process-wide singleton over the WorldQuant Brain doc corpus."""

    _instance: "WQBrainDocsRAG | None" = None
    _lock = Lock()

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else _DEFAULT_DOCS_ROOT
        self._kbs: list[WQKnowledgeBase] = []
        self._loaded = False

    @classmethod
    def shared(cls) -> "WQBrainDocsRAG":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def load(self) -> None:
        if self._loaded:
            return
        roots: list[Path] = []
        if self.root.exists():
            roots.append(self.root)
        for extra in _SECONDARY_ROOTS:
            if extra.exists():
                roots.append(extra)
        for root in roots:
            kb = WQKnowledgeBase(root)
            kb.load_all()
            self._kbs.append(kb)
        self._loaded = True

    @property
    def is_empty(self) -> bool:
        if not self._loaded:
            self.load()
        return not any(kb.documents for kb in self._kbs)

    def query(self, query: str, k: int = 4) -> str:
        if not self._loaded:
            self.load()
        snippets: list[str] = []
        per_kb = max(1, k // max(1, len(self._kbs))) if self._kbs else k
        for kb in self._kbs:
            ctx = kb.query_context(query, k=per_kb)
            if ctx:
                snippets.append(ctx)
        return "\n\n===\n\n".join(snippets)

    def prompt_block(self, query: str, k: int = 4, *, header: str = "WORLDQUANT BRAIN DOCS") -> str:
        """Return a prompt-ready block, or empty string when corpus is empty."""
        ctx = self.query(query, k=k).strip()
        if not ctx:
            return ""
        return f"=== {header} (authoritative) ===\n{ctx}\n=== END {header} ===\n"


def get_wq_docs_context(query: str, k: int = 4) -> str:
    """Convenience accessor used by Hermes bridge and LLM generator."""
    try:
        return WQBrainDocsRAG.shared().prompt_block(query, k=k)
    except Exception:  # pragma: no cover - RAG must never break generation
        return ""
