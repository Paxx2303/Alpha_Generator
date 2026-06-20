"""Research tools: knowledge search and WQB data field discovery."""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import MCP_SKILL_PATH


def get_skill_knowledge() -> str:
    """
    Return the complete mcp_skill.md knowledge base.

    Contains: operator docs, core rules, valid/broken operators,
    optimisation techniques, proven settings grid, composite alpha examples.

    IMPORTANT: Call this at the start of every research session.
    """
    if MCP_SKILL_PATH.exists():
        return MCP_SKILL_PATH.read_text(encoding="utf-8")
    legacy = _ROOT / "docs" / "legacy_sources.md"
    if legacy.exists():
        return legacy.read_text(encoding="utf-8")
    return "No skill knowledge found. Run scripts/export_legacy.py first."


def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """
    Semantic search of the knowledge base (ChromaDB).

    Returns the top_k most relevant chunks — academic theories,
    operator usage patterns, proven alpha strategies.

    Always call this before generating a new hypothesis.
    """
    try:
        from core.knowledge.vector_store import VectorStore
        vs = VectorStore()
        results = vs.search(query, top_k=top_k)
        if not results:
            return f"No results found for: {query}"
        lines = [f"## Top {len(results)} results for: {query}\n"]
        for i, r in enumerate(results, 1):
            meta = r.get("metadata", {})
            lines.append(f"**[{i}]** (score={r.get('score', 0):.3f}) "
                         f"*{meta.get('source_type','?')} / {meta.get('category','?')}*")
            lines.append(r.get("content", ""))
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Knowledge search error: {e}"


def search_data_fields(query: str, limit: int = 20) -> list:
    """
    Search WorldQuant Brain for available data fields
    (fundamentals, sentiment, estimates, technicals, etc.).

    Use this to discover real variable names before writing alpha formulas.
    """
    try:
        from wqb_automation import WQBAutomation, load_config
        config = load_config()
        config["headless"] = True
        auto = WQBAutomation(config)
        auto.start()
        result = auto.search_data_fields(query, limit)
        auto.stop()
        return result
    except Exception as e:
        return [{"error": str(e)}]
