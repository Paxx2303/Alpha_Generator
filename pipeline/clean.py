# pipeline/clean.py — Clean & validate raw documents
import re
import shutil
from pathlib import Path
from typing import Tuple

from config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    MIN_WORDS_PER_DOC,
    MAX_WORDS_PER_DOC,
    NOISE_PATTERNS,
)
from .base import StepResult


# Pre-compile noise patterns once
_NOISE_RE = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in NOISE_PATTERNS]

# HTML / boilerplate regexes
_BOILERPLATE_RE = [
    re.compile(r"---+\s*\n.*?Sign in.*?\n---+", re.DOTALL | re.IGNORECASE),
    re.compile(r"Footer navigation.*$", re.DOTALL | re.IGNORECASE),
    re.compile(r"<[^>]+>"),                        # HTML tags
    re.compile(r"\n{3,}", re.MULTILINE),            # excessive blank lines → \n\n
    re.compile(r" {2,}"),                           # multiple spaces → 1
]


def is_noise(content: str) -> bool:
    """Return True if ANY noise pattern matches the content (case-insensitive)."""
    lower = content.lower()
    for pattern in _NOISE_RE:
        if pattern.search(lower):
            return True
    return False


def clean_document(content: str) -> Tuple[str, list]:
    """
    Clean a document and return (cleaned_content, warnings).

    Warnings are short strings like "short_doc:42" or "no_headings".
    """
    warnings = []

    # 1. Fix encoding
    content = content.encode("utf-8", errors="replace").decode("utf-8")

    # 2. Remove boilerplate / HTML
    replacements = [
        (_BOILERPLATE_RE[0], ""),        # sign-in banners
        (_BOILERPLATE_RE[1], ""),        # footer nav
        (_BOILERPLATE_RE[2], ""),        # HTML tags
        (_BOILERPLATE_RE[3], "\n\n"),    # blank lines
        (_BOILERPLATE_RE[4], " "),       # multiple spaces
    ]
    for pattern, repl in replacements:
        content = pattern.sub(repl, content)

    content = content.strip()

    # 3. Validate
    word_count = len(content.split())
    if word_count < MIN_WORDS_PER_DOC:
        warnings.append(f"short_doc:{word_count}")
    if word_count > MAX_WORDS_PER_DOC:
        warnings.append(f"long_doc:{word_count}")
    if not re.search(r"^#", content, re.MULTILINE):
        warnings.append("no_headings")

    return content, warnings


def check_quality(file_path: Path) -> Tuple[bool, str]:
    """
    Gate-check a file before it is copied to processed/.
    Returns (passes, reason).
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return False, f"Read error: {e}"

    if is_noise(content):
        return False, "Matches noise pattern"

    word_count = len(content.split())
    if word_count < MIN_WORDS_PER_DOC:
        return False, f"Too short ({word_count} words, need ≥{MIN_WORDS_PER_DOC})"
    if word_count > MAX_WORDS_PER_DOC:
        return False, f"Too long ({word_count} words, need ≤{MAX_WORDS_PER_DOC}) — needs chunking"

    headings = [l for l in content.split("\n") if l.startswith("#")]
    if word_count > 500 and not headings:
        return False, "No headings — hard to chunk later"

    return True, "OK"


class CleanStep:
    """
    Pipeline step: Copy raw docs → processed_data/ after cleaning + quality gate.

    Walks every .md / .txt file under RAW_DATA_DIR.  Only files that pass the
    quality gate are written to PROCESSED_DATA_DIR (preserving sub-folder structure).
    """

    def run(self) -> StepResult:
        stats = {"processed": 0, "excluded": 0, "warnings": 0}
        errors = []

        for raw_file in RAW_DATA_DIR.rglob("*"):
            if raw_file.suffix not in {".md", ".txt"}:
                continue

            passes, reason = check_quality(raw_file)
            if not passes:
                stats["excluded"] += 1
                continue

            # Read, clean, write
            try:
                content = raw_file.read_text(encoding="utf-8", errors="ignore")
                cleaned, warns = clean_document(content)

                # Derive output path (mirror sub-folder structure)
                rel = raw_file.relative_to(RAW_DATA_DIR)
                out_path = PROCESSED_DATA_DIR / rel
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(cleaned, encoding="utf-8")

                stats["processed"] += 1
                stats["warnings"] += len(warns)
            except Exception as e:
                errors.append(f"{raw_file.name}: {e}")
                stats["excluded"] += 1

        summary = (
            f"Processed {stats['processed']} files, "
            f"excluded {stats['excluded']}, "
            f"{stats['warnings']} warnings."
        )
        if errors:
            summary += f"  Errors: {'; '.join(errors[:3])}"

        return StepResult(success=True, summary=summary, stats=stats)
