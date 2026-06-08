# pipeline/chunk.py — Split documents into RAG-ready chunks
import json
import re
from pathlib import Path
from typing import List

from config import (
    PROCESSED_DATA_DIR,
    CHUNKS_DIR,
    MIN_CHUNK_WORDS,
    MAX_CHUNK_WORDS,
)
from .base import StepResult


def chunk_document(content: str, source: str) -> List[dict]:
    """
    Split a document into chunks suitable for vector indexing.

    Strategy (in priority order):
      1. Split on '## ' headings (H2).
      2. If a section is still > MAX_CHUNK_WORDS, split further on '### ' (H3).
      3. Discard sections with fewer than MIN_CHUNK_WORDS words.

    Each chunk carries:
      content      — the text of the chunk
      metadata     — source path, chunk_index, word_count, chunk_type
    """
    chunks: List[dict] = []

    # Split on H2 headings (keep the heading line in the chunk)
    sections = re.split(r"\n(?=## )", content.strip())

    for i, section in enumerate(sections):
        word_count = len(section.split())

        if word_count > MAX_CHUNK_WORDS:
            # Further split on H3 headings
            sub_sections = re.split(r"\n(?=### )", section)
            for j, sub in enumerate(sub_sections):
                sub = sub.strip()
                if not sub:
                    continue
                sub_words = len(sub.split())
                if sub_words >= MIN_CHUNK_WORDS:
                    chunks.append({
                        "content": sub,
                        "metadata": {
                            "source": source,
                            "chunk_index": f"{i}.{j}",
                            "word_count": sub_words,
                            "chunk_type": "subsection",
                        },
                    })

        elif word_count >= MIN_CHUNK_WORDS:
            chunks.append({
                "content": section.strip(),
                "metadata": {
                    "source": source,
                    "chunk_index": str(i),
                    "word_count": word_count,
                    "chunk_type": "section",
                },
            })
        # else: section too short — discard

    return chunks


class ChunkStep:
    """
    Pipeline step: Read all .md files from PROCESSED_DATA_DIR,
    split into chunks, and write to CHUNKS_DIR.

    Output: one JSON file per source document at CHUNKS_DIR/<relative_path>.json,
            plus a master chunks_index.json.
    """

    def run(self) -> StepResult:
        stats = {"docs": 0, "chunks": 0, "skipped": 0}
        all_chunks: List[dict] = []

        for doc_path in PROCESSED_DATA_DIR.rglob("*.md"):
            try:
                content = doc_path.read_text(encoding="utf-8", errors="ignore")
                rel     = doc_path.relative_to(PROCESSED_DATA_DIR)
                source  = str(rel)

                doc_chunks = chunk_document(content, source)
                if not doc_chunks:
                    stats["skipped"] += 1
                    continue

                # Save per-document chunk file
                out_path = CHUNKS_DIR / rel.with_suffix(".json")
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(
                    json.dumps(doc_chunks, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

                all_chunks.extend(doc_chunks)
                stats["docs"]   += 1
                stats["chunks"] += len(doc_chunks)

            except Exception:
                stats["skipped"] += 1
                continue

        # Master index
        master = CHUNKS_DIR / "chunks_index.json"
        CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
        master.write_text(
            json.dumps({"total": len(all_chunks), "chunks": all_chunks}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        summary = (
            f"Chunked {stats['docs']} docs → {stats['chunks']} chunks. "
            f"Skipped {stats['skipped']}. Index: {master.name}"
        )
        return StepResult(success=True, summary=summary, stats=stats)
