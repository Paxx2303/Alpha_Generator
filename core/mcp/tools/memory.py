"""Memory tools: persist lessons and theories across research sessions."""
import json
import sys
from datetime import datetime, UTC
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import MCP_SKILL_PATH

THEORY_LOG_PATH = _ROOT / "data" / "theory_log.json"


def update_skill(lesson: str, category: str = "general") -> str:
    """
    Append a new lesson / finding to mcp_skill.md so knowledge persists across sessions.

    Args:
        lesson:   Insight to record (e.g. "ts_min is broken on WQB, use ts_arg_min instead").
        category: Tag — one of: operator, field, settings, strategy, source, general.
    """
    try:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d")
        entry = f"\n### [{timestamp}] [{category.upper()}]\n{lesson}\n"
        with open(MCP_SKILL_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"Lesson recorded [{category.upper()}] on {timestamp}."
    except Exception as e:
        return f"Error writing to mcp_skill.md: {e}"


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
    THEORY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if THEORY_LOG_PATH.exists():
        with open(THEORY_LOG_PATH, encoding="utf-8") as f:
            theories = json.load(f)
    else:
        theories = []

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

    with open(THEORY_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(theories, f, indent=2, ensure_ascii=False)

    return f"Theory '{title}' saved (id={entry['id']}, confidence={confidence})."
