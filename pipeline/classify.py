# pipeline/classify.py — Categorize documents + compute quality score
import re
import json
from pathlib import Path
from typing import Tuple

from config import (
    PROCESSED_DATA_DIR,
    CATEGORIES,
    WQB_FORMULA_PATTERNS,
    SOURCE_QUALITY_MAP,
)
from .base import StepResult


# Pre-compile WQB formula patterns once
_WQB_RE = [re.compile(p) for p in WQB_FORMULA_PATTERNS]


def categorize_file(file_path: Path) -> str:
    """
    Return the best-fit category name for a document.

    Scoring is weighted:
      - Title (first 5 lines)  → weight ×3
      - Markdown headings       → weight ×2
      - Full body               → weight ×1

    Falls back to 'research_insights' when no category wins.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return "research_insights"

    lines = content.split("\n")
    title_text  = " ".join(lines[:5]).lower()
    header_text = " ".join(l for l in lines if l.startswith("#")).lower()
    body_text   = content.lower()

    category_scores: dict[str, int] = {}
    for category, info in CATEGORIES.items():
        score = 0
        for kw in info["keywords"]:
            score += title_text.count(kw)  * 3
            score += header_text.count(kw) * 2
            score += body_text.count(kw)   * 1
        category_scores[category] = score

    if max(category_scores.values(), default=0) == 0:
        return "research_insights"
    return max(category_scores, key=category_scores.get)


def compute_quality_score(content: str, metadata: dict) -> int:
    """
    Compute a 0–100 quality score for a document.

    Breakdown:
      +40  WQB formula operators present (10 pts each, capped)
      +20  Sharpe / Fitness metrics mentioned
      +20  Economic explanation keywords present
      +20  Source type quality
    """
    score = 0

    # WQB formula operators (+40 max)
    formula_count = sum(1 for p in _WQB_RE if p.search(content))
    score += min(formula_count * 10, 40)

    # Sharpe / Fitness metrics (+20)
    if re.search(r"sharpe[:\s]+[\d.]+", content, re.IGNORECASE):
        score += 10
    if re.search(r"fitness[:\s]+[\d.]+", content, re.IGNORECASE):
        score += 10

    # Economic explanation (+20)
    explanation_keywords = [
        "because", "therefore", "hypothesis", "intuition",
        "economic", "rationale", "explanation", "suggests",
    ]
    if any(kw in content.lower() for kw in explanation_keywords):
        score += 20

    # Source type (+20)
    source_type = metadata.get("source_type", "")
    score += SOURCE_QUALITY_MAP.get(source_type, 0)

    return min(score, 100)


def parse_metadata_header(content: str) -> dict:
    """
    Parse a YAML-like front-matter block at the top of a markdown file.

    Expected format:
        ---
        source: https://...
        source_type: paper
        ingested_at: 2026-06-06
        quality_note: ...
        ---
    Returns a dict (may be empty if no front-matter found).
    """
    metadata: dict = {}
    if not content.startswith("---"):
        return metadata

    end = content.find("---", 3)
    if end == -1:
        return metadata

    header = content[3:end]
    for line in header.strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()
    return metadata


class ClassifyStep:
    """
    Pipeline step: For every file in PROCESSED_DATA_DIR, attach category +
    quality_score metadata into a sidecar JSON index file.

    Output: PROCESSED_DATA_DIR / classification_index.json
    """

    def run(self) -> StepResult:
        index = []
        stats = {"classified": 0, "skipped": 0}

        for doc_path in PROCESSED_DATA_DIR.rglob("*.md"):
            try:
                content = doc_path.read_text(encoding="utf-8", errors="ignore")
                meta = parse_metadata_header(content)
                category = categorize_file(doc_path)
                quality  = compute_quality_score(content, meta)

                index.append({
                    "file": str(doc_path.relative_to(PROCESSED_DATA_DIR)),
                    "category": category,
                    "quality_score": quality,
                    "metadata": meta,
                })
                stats["classified"] += 1
            except Exception as e:
                stats["skipped"] += 1
                continue

        # Persist index
        out = PROCESSED_DATA_DIR / "classification_index.json"
        out.write_text(
            json.dumps({"documents": index}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        summary = (
            f"Classified {stats['classified']} documents, "
            f"skipped {stats['skipped']}. "
            f"Index saved to {out.name}."
        )
        return StepResult(success=True, summary=summary, stats=stats)
