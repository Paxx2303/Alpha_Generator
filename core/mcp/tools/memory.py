"""Memory tools: persist lessons and theories across research sessions."""
import json
import sys
from datetime import datetime, timezone
UTC = timezone.utc
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

THEORY_LOG_PATH = _ROOT / "data" / "theory_log.json"


def _load_theories() -> list:
    if THEORY_LOG_PATH.exists():
        with open(THEORY_LOG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def _write_theories(theories: list) -> None:
    THEORY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(THEORY_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(theories, f, indent=2, ensure_ascii=False)


def update_skill(lesson: str, category: str = "general") -> str:
    """
    Record a quick empirical lesson from a simulation session.
    Saved as a low-confidence theory in theory_log.json so it persists across sessions.

    Args:
        lesson:   Insight to record (e.g. "ts_min is broken on WQB, use ts_arg_min instead").
        category: Tag — one of: operator, field, settings, strategy, source, general.
    """
    theories = _load_theories()
    entry = {
        "id": f"t{len(theories)+1:04d}",
        "title": f"[{category.upper()}] {lesson[:80]}",
        "body": lesson,
        "confidence": 0.3,
        "source_url": "",
        "tags": [category, "lesson"],
        "created_at": datetime.now(UTC).isoformat(),
    }
    theories.append(entry)
    _write_theories(theories)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"Lesson recorded [{category.upper()}] on {timestamp} (id={entry['id']})."


def save_theory(
    title: str,
    body: str,
    confidence: float = 0.5,
    source_url: str = "",
    tags: list = None,
) -> str:
    """
    Save a research theory to the Theory Notebook (data/theory_log.json).
    Visible on the Theory Notebook page of the observation dashboard.

    Args:
        title:      Short title (e.g. "Earnings Surprise → Next-Day Reversal").
        body:       Human-readable explanation (plain language, 2-5 sentences).
        confidence: 0.0–1.0 based on evidence strength.
        source_url: URL of the source paper / blog that inspired this theory.
        tags:       List of tags e.g. ["momentum", "earnings", "reversal"].
    """
    theories = _load_theories()
    entry = {
        "id": f"t{len(theories)+1:04d}",
        "title": title,
        "body": body,
        "confidence": float(confidence),
        "source_url": source_url,
        "tags": tags or [],
        "created_at": datetime.now(UTC).isoformat(),
    }
    theories.append(entry)
    _write_theories(theories)
    return f"Theory '{title}' saved (id={entry['id']}, confidence={confidence})."
