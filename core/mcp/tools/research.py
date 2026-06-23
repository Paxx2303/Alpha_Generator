"""Research tools: data field search + empirical knowledge retrieval."""
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

THEORY_LOG_PATH = _ROOT / "data" / "theory_log.json"

# Reuse the shared WQB session from alpha tools — one login, shared across all tools.
from core.mcp.tools.alpha import _get_automation  # noqa: E402


def search_data_fields(query: str, limit: int = 20) -> str:
    """
    Search WorldQuant Brain for available data fields matching a keyword.

    Use this to verify field names exist before writing formulas.
    Returns JSON list with field id, description, dataset, type.

    Args:
        query: keyword to search (e.g. "earnings", "eps", "revenue", "vwap")
        limit: max results to return (default 20)
    """
    try:
        auto = _get_automation()
        results = auto.search_data_fields(query, limit)
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_skill_knowledge(topic: str = "", market_setting: str = "") -> str:
    """
    Retrieve empirical knowledge from this session's research history.

    Call this BEFORE forming a hypothesis (check what's already known) AND
    AFTER a backtest (compare result vs existing theories).

    Args:
        topic:          filter theories by keyword (e.g. "momentum", "earnings")
                        leave empty to get all recent knowledge
        market_setting: filter by setting string (e.g. "TOP1000|INDUSTRY|3|0.08")
                        leave empty to get cross-setting knowledge

    Returns structured summary:
      - recent_theories: theories sorted by confidence (high first)
      - gold_alphas:     gold alphas in this setting (for correlation awareness)
      - failed_patterns: known-bad formula+setting combos to avoid
      - current_session: what's been tested in the current hour's setting
    """
    try:
        result = {
            "recent_theories": _get_theories(topic),
            "gold_alphas": _get_gold_alphas(market_setting),
            "failed_patterns": _get_recent_failures(market_setting),
            "platform_constraints": _platform_constraints(),
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _get_theories(topic: str) -> list:
    if not THEORY_LOG_PATH.exists():
        return []
    with open(THEORY_LOG_PATH, encoding="utf-8") as f:
        theories = json.load(f)
    if topic:
        kw = topic.lower()
        theories = [
            t for t in theories
            if kw in t.get("title", "").lower()
            or kw in t.get("body", "").lower()
            or any(kw in tag.lower() for tag in t.get("tags", []))
        ]
    # Sort by confidence desc, return top 10
    theories.sort(key=lambda t: t.get("confidence", 0), reverse=True)
    return theories[:10]


def _get_gold_alphas(market_setting: str) -> list:
    try:
        from storage.store import Store
        s = Store()
        alphas = s.get_gold_alphas()
        s.close()
        if market_setting and alphas:
            setting_prefix = market_setting.split("|")[0]  # e.g. "TOP1000"
            alphas = [a for a in alphas if a.get("settings", "").startswith(setting_prefix)]
        return alphas[:10]
    except Exception:
        return []


def _get_recent_failures(market_setting: str) -> list:
    try:
        from storage.store import Store
        s = Store()
        cursor = s.conn.execute(
            "SELECT formula, settings, sharpe, fitness FROM failed_alphas "
            "WHERE settings LIKE ? ORDER BY rowid DESC LIMIT 20",
            (f"{market_setting.split('|')[0]}%",) if market_setting else ("%",),
        )
        rows = [dict(r) for r in cursor.fetchall()]
        s.close()
        return rows
    except Exception:
        return []


def _platform_constraints() -> dict:
    return {
        "broken_operators": ["ts_min", "ts_max", "delay"],
        "gold_criteria": "Sharpe >= 1.25 AND Fitness >= 1.0 AND Turnover 10-70%",
        "fitness_formula": "Sharpe × sqrt(|Returns| / max(Turnover, 0.125))",
        "self_correlation_cutoff": 0.7,
        "mandatory_transforms": "rank() → group_neutralize() → truncate(0.08)",
        "proven_setting": "TOP1000|INDUSTRY|3|0.08",
    }
