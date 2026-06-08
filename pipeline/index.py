# pipeline/index.py — Build the search index (inverted bigram index) from chunks
import json
import re
from pathlib import Path

from config import CHUNKS_DIR, FINAL_DATASET_DIR, RANDOM_SEED, TRAIN_RATIO, VAL_RATIO
from .base import StepResult


def build_ngrams(text: str, n: int = 2) -> list:
    """
    Build unigrams + bigrams from text.

    Unigrams  — all lowercase words ≥ 3 characters
    Bigrams   — consecutive word pairs joined by '_'

    Using bigrams prevents 'sharpe_ratio' from matching a document that
    only contains the words 'sharpe' or 'ratio' independently.
    """
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    unigrams = words
    bigrams  = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
    return unigrams + bigrams


def build_search_index(chunks: list) -> dict:
    """
    Build an inverted index: token → list of chunk indices.
    Input chunks are the full list from chunks_index.json.
    """
    index: dict = {}
    for i, chunk in enumerate(chunks):
        tokens = set(build_ngrams(chunk.get("content", "")))
        for token in tokens:
            index.setdefault(token, []).append(i)
    return index


def create_training_splits(documents: list, seed: int = RANDOM_SEED) -> dict:
    """
    Stratified shuffle-split 70/20/10.

    • Groups docs by category first so each split contains a proportional
      representation of every category.
    • Uses a fixed seed for reproducibility.
    """
    import random
    random.seed(seed)

    by_category: dict = {}
    for doc in documents:
        cat = doc.get("metadata", {}).get("category", "unknown")
        by_category.setdefault(cat, []).append(doc)

    splits: dict = {"train": [], "validation": [], "test": []}
    for cat, docs in by_category.items():
        random.shuffle(docs)          # ← shuffle BEFORE split (fix from guide)
        n = len(docs)
        train_end = int(TRAIN_RATIO * n)
        val_end   = int((TRAIN_RATIO + VAL_RATIO) * n)
        splits["train"].extend(docs[:train_end])
        splits["validation"].extend(docs[train_end:val_end])
        splits["test"].extend(docs[val_end:])

    return splits


class IndexStep:
    """
    Pipeline step: Build search index + training splits from chunked data.

    Reads: CHUNKS_DIR/chunks_index.json
    Writes:
      FINAL_DATASET_DIR/search_index.json
      FINAL_DATASET_DIR/train_split.json
      FINAL_DATASET_DIR/validation_split.json
      FINAL_DATASET_DIR/test_split.json
      FINAL_DATASET_DIR/alpha_research_dataset.json  (master dataset)
    """

    def run(self) -> StepResult:
        chunks_file = CHUNKS_DIR / "chunks_index.json"
        if not chunks_file.exists():
            return StepResult(
                success=False,
                summary="chunks_index.json not found — run ChunkStep first.",
                error="Missing chunks_index.json",
            )

        try:
            data   = json.loads(chunks_file.read_text(encoding="utf-8"))
            chunks = data.get("chunks", [])

            FINAL_DATASET_DIR.mkdir(parents=True, exist_ok=True)

            # ── Search index ───────────────────────────────────────────────────
            index = build_search_index(chunks)
            (FINAL_DATASET_DIR / "search_index.json").write_text(
                json.dumps(index, ensure_ascii=False),
                encoding="utf-8",
            )

            # ── Training splits ────────────────────────────────────────────────
            # Treat each chunk as a "document" for the split
            splits = create_training_splits(chunks)
            for split_name, docs in splits.items():
                (FINAL_DATASET_DIR / f"{split_name}_split.json").write_text(
                    json.dumps({"total": len(docs), "documents": docs}, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

            # ── Master dataset ─────────────────────────────────────────────────
            master = {
                "total_chunks": len(chunks),
                "index_tokens": len(index),
                "splits": {k: len(v) for k, v in splits.items()},
                "documents": chunks,
            }
            (FINAL_DATASET_DIR / "alpha_research_dataset.json").write_text(
                json.dumps(master, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            summary = (
                f"Indexed {len(index)} tokens from {len(chunks)} chunks. "
                f"Splits — train: {len(splits['train'])}, "
                f"val: {len(splits['validation'])}, "
                f"test: {len(splits['test'])}."
            )
            return StepResult(success=True, summary=summary, stats={"tokens": len(index), "chunks": len(chunks)})

        except Exception as e:
            return StepResult(success=False, summary=str(e), error=str(e))
