# alpha_skills/knowledge_retriever.py — RAG retrieval with 3-layer scoring
import json
import math
import os
import re
from pathlib import Path
from typing import List, Dict

# Allow running standalone (outside pipeline context) by adjusting sys.path
import sys
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config import (
    FINAL_DATASET_DIR,
    REFERENCE_DIR,
    TOP_K_RESULTS,
    RAG_SIM_WEIGHT,
    RAG_LENGTH_PENALTY_WEIGHT,
    RAG_QUALITY_WEIGHT,
    IDEAL_CHUNK_WORDS,
    MIN_QUALITY_FOR_IMPORTANT,
)
from pipeline.index import build_ngrams


# ── Helpers ────────────────────────────────────────────────────────────────────

def length_penalty(text: str, ideal_tokens: int = IDEAL_CHUNK_WORDS) -> float:
    """
    Log-normal penalty (0.0–1.0) where peak = 1.0 at ideal_tokens.
    Penalises both very short and very long chunks.
    """
    token_count = len(text.split())
    if token_count == 0:
        return 0.0
    ratio = token_count / ideal_tokens
    return math.exp(-0.5 * (math.log(max(ratio, 0.01)) ** 2))


def keyword_similarity(query_terms: List[str], document_text: str) -> float:
    """
    Simple TF-style similarity: count of query-term (+ bigram) hits in document.
    Normalised to [0, 1] by dividing by (n_terms × expected_density).
    """
    doc_lower = document_text.lower()

    # Build query bigrams so "sharpe ratio" matches as a unit
    query_unigrams = [t.lower() for t in query_terms]
    query_bigrams  = [
        f"{query_terms[i].lower()}_{query_terms[i+1].lower()}"
        for i in range(len(query_terms) - 1)
    ]
    all_query_tokens = query_unigrams + query_bigrams

    raw = sum(len(re.findall(re.escape(t), doc_lower)) for t in all_query_tokens)

    # Normalise: assume a good result contains each token ~2×
    expected = max(len(all_query_tokens) * 2, 1)
    return min(raw / expected, 1.0)


# ── Retriever ──────────────────────────────────────────────────────────────────

class KnowledgeRetriever:
    """
    Search the knowledge base and rank results using 3-layer scoring:

      final_score = sim * SIM_WEIGHT
                  + length_penalty * LENGTH_WEIGHT
                  + quality_score * QUALITY_WEIGHT
    """

    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            self.skills_dir = Path(__file__).parent
        else:
            self.skills_dir = Path(skills_dir)

        # These are resolved relative to the skills_dir or from config
        self.final_dataset_dir = FINAL_DATASET_DIR
        self.reference_dir     = self.skills_dir / "reference"
        self.dataset_file      = self.final_dataset_dir / "alpha_research_dataset.json"

    # ── Public API ─────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = TOP_K_RESULTS, min_quality: int = 0) -> str:
        """
        Search the knowledge base for `query`.

        Args:
            query:       Free-text search query.
            top_k:       Number of results to return.
            min_quality: Minimum quality_score for results (0 = no filter).

        Returns a human-readable markdown string with the top results.
        """
        query_terms = query.split()
        candidates  = self._gather_candidates()

        # Score every candidate
        scored: List[tuple] = []
        for doc in candidates:
            content = doc.get("content", "")
            meta    = doc.get("metadata", {})

            sim     = keyword_similarity(query_terms, content)
            penalty = length_penalty(content)
            quality = meta.get("quality_score", 50) / 100.0

            final = (
                sim     * RAG_SIM_WEIGHT
                + penalty * RAG_LENGTH_PENALTY_WEIGHT
                + quality * RAG_QUALITY_WEIGHT
            )
            if sim == 0:          # Skip completely irrelevant docs
                continue
            if quality * 100 < min_quality:
                continue

            scored.append((doc, final))

        # Sort and take top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        top_results = scored[:top_k]

        if not top_results:
            return f"No results found for query: '{query}'"

        lines = [f"### Top {len(top_results)} Results for '{query}'\n"]
        for i, (doc, score) in enumerate(top_results, 1):
            meta    = doc.get("metadata", {})
            title   = meta.get("title", meta.get("source", f"Document {i}"))
            quality = meta.get("quality_score", "N/A")
            content = doc.get("content", "")
            if len(content) > 1000:
                content = content[:1000] + "\n...[truncated]"

            lines += [
                f"#### Result {i}: {title}",
                f"**Score:** {score:.3f}  |  **Quality:** {quality}  |  **Source:** {meta.get('source', 'unknown')}",
                f"\n{content}\n",
                "---",
            ]
        return "\n".join(lines)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _gather_candidates(self) -> List[Dict]:
        """Combine JSON dataset docs + markdown reference files."""
        candidates: List[Dict] = []
        candidates.extend(self._load_json_dataset())
        candidates.extend(self._load_markdown_references())
        return candidates

    def _load_json_dataset(self) -> List[Dict]:
        docs: List[Dict] = []
        if not self.dataset_file.exists():
            return docs
        try:
            data = json.loads(self.dataset_file.read_text(encoding="utf-8"))
            for doc in data.get("documents", []):
                meta = doc.get("metadata", {})
                # Normalise: ensure quality_score is present
                if "quality_score" not in meta:
                    meta["quality_score"] = 50
                docs.append({
                    "content":  doc.get("content", ""),
                    "metadata": {
                        "title":         meta.get("title", doc.get("id", "unknown")),
                        "source":        f"dataset/{meta.get('category', 'unknown')}",
                        "quality_score": meta.get("quality_score", 50),
                    },
                })
        except Exception as e:
            print(f"[KnowledgeRetriever] Error reading JSON dataset: {e}")
        return docs

    def _load_markdown_references(self) -> List[Dict]:
        docs: List[Dict] = []
        if not self.reference_dir.exists():
            return docs
        try:
            for file_path in self.reference_dir.rglob("*.md"):
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                title = title_match.group(1) if title_match else file_path.name
                docs.append({
                    "content":  content,
                    "metadata": {
                        "title":         title,
                        "source":        f"reference/{file_path.name}",
                        "quality_score": 50,   # Default for reference files
                    },
                })
        except Exception as e:
            print(f"[KnowledgeRetriever] Error reading markdown references: {e}")
        return docs


# ── Standalone test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    retriever = KnowledgeRetriever()
    print(retriever.search("momentum mean reversion", top_k=2))
