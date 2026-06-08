# mcp_server.py — Alpha Generator MCP Server
import json
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ── Path setup (all paths from config, no hardcoding) ─────────────────────────
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "alpha_skills") not in sys.path:
    sys.path.insert(0, str(_ROOT / "alpha_skills"))

from config import MCP_SKILL_PATH, GOLD_ALPHAS_PATH
from wqb_automation import WQBAutomation, load_config

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("Alpha Generator Server")

# ── Singleton WQB client ───────────────────────────────────────────────────────
_auto_instance  = None
_is_logged_in   = False


def get_automation() -> WQBAutomation:
    global _auto_instance, _is_logged_in
    if _auto_instance is None:
        logging.info("Initialising WQBAutomation…")
        config = load_config()
        config["headless"] = True
        _auto_instance = WQBAutomation(config)
        _auto_instance.start()

    if not _is_logged_in:
        logging.info("Logging into WorldQuant Brain…")
        _is_logged_in = _auto_instance.login()
        if not _is_logged_in:
            logging.error("Failed to log in to WorldQuant Brain")

    return _auto_instance


# ── Tools ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_skill_knowledge() -> str:
    """
    Return the complete mcp_skill.md knowledge base.

    Contains: tool docs, core rules, valid/broken operators,
    optimisation techniques, proven settings grid, and composite alpha examples.

    IMPORTANT: Call this at the start of every session.
    """
    try:
        if MCP_SKILL_PATH.exists():
            return MCP_SKILL_PATH.read_text(encoding="utf-8")
        return "Error: mcp_skill.md not found"
    except Exception as e:
        return f"Error reading skill file: {e}"


@mcp.tool()
def search_data_fields(query: str, limit: int = 20) -> list:
    """
    Search WorldQuant Brain for available data fields
    (fundamentals, sentiment, estimates, etc.).

    Use this to discover real variable names for alpha formulas.
    """
    try:
        auto = get_automation()
        return auto.search_data_fields(query, limit)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Search the internal knowledge base (academic papers, reference docs,
    processed datasets) for alpha theories and economic rationale.

    ALWAYS call this before generating a new hypothesis.
    """
    try:
        from knowledge_retriever import KnowledgeRetriever
        retriever = KnowledgeRetriever()
        return retriever.search(query, top_k)
    except Exception as e:
        return f"Error searching knowledge base: {e}"


@mcp.tool()
def submit_alpha(formula: str, settings: dict = None, dry_run: bool = True) -> str:
    """
    Submit an alpha formula to WorldQuant Brain for simulation.

    Set dry_run=True (default) to validate without submitting.
    Default settings: TOP3000 | Market | Decay 0 | Truncation 0.05.
    """
    if dry_run:
        return json.dumps(
            {"message": "Dry-run mode — no submission made.", "formula": formula, "settings": settings},
            indent=2,
        )

    try:
        auto = get_automation()
        if not settings:
            settings = {"universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05}

        settings_str = (
            f"{settings.get('universe', 'TOP3000')}|"
            f"{settings.get('neutralization', 'Market')}|"
            f"{settings.get('decay', 0)}|"
            f"{settings.get('truncation', 0.05)}"
        )
        logging.info(f"Submitting formula: {formula}  settings: {settings_str}")
        result = auto.submit_alpha(formula, settings_str)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def diagnose_alpha(metrics: dict) -> dict:
    """
    Analyse alpha backtest metrics and return a structured diagnosis.

    Pass a dict with keys: sharpe, fitness, turnover, drawdown.
    Returns: pass/fail verdict, list of issues, and concrete fix recommendations.

    Example:
        diagnose_alpha({"sharpe": 0.91, "fitness": 0.34, "turnover": 32.6, "drawdown": 7.5})
    """
    try:
        from agent.tools.diagnose_alpha import diagnose_alpha as _diagnose
        return _diagnose(metrics)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def update_skill(lesson: str, category: str = "general") -> str:
    """
    Append a new lesson / finding to mcp_skill.md so the agent learns
    from experience across sessions.

    Args:
        lesson:   The insight to record (e.g. "ts_min is broken, use -ts_arg_min instead").
        category: Tag for the lesson (e.g. "operator", "settings", "field", "strategy").
    """
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        entry = f"\n### [{timestamp}] [{category.upper()}]\n{lesson}\n"

        with open(MCP_SKILL_PATH, "a", encoding="utf-8") as f:
            f.write(entry)

        return f"Lesson recorded under [{category.upper()}] on {timestamp}."
    except Exception as e:
        return f"Error writing to mcp_skill.md: {e}"


@mcp.tool()
def get_gold_alphas() -> str:
    """
    Return past successful alphas (Sharpe ≥ 1.25, Fitness ≥ 1.0) from gold_alphas.json.

    Use these as inspiration or as mutation seeds.
    """
    try:
        if GOLD_ALPHAS_PATH.exists():
            return GOLD_ALPHAS_PATH.read_text(encoding="utf-8")
        return "gold_alphas.json not found."
    except Exception as e:
        return f"Error reading gold alphas: {e}"


@mcp.tool()
def mutate_formula(formula: str, n: int = 3) -> list:
    """
    Auto-generate `n` variations of a formula using 4 mutation strategies:
      1. Shorter lookback  (×0.6)
      2. Longer lookback   (×2)
      3. Replace 'close' with 'vwap'
      4. Add volatility normalisation

    Returns a list of formula strings.
    """
    import re

    mutations = []

    # Find a numeric lookback in the formula
    lookback_match = re.search(r",\s*(\d+)\s*\)", formula)
    if lookback_match:
        orig_lb = int(lookback_match.group(1))

        # Mutation 1: shorter lookback
        short_lb = max(1, round(orig_lb * 0.6))
        mutations.append(formula.replace(f", {orig_lb})", f", {short_lb})"))

        # Mutation 2: longer lookback
        long_lb = round(orig_lb * 2)
        mutations.append(formula.replace(f", {orig_lb})", f", {long_lb})"))

    # Mutation 3: close → vwap
    if "close" in formula:
        mutations.append(formula.replace("close", "vwap"))

    # Mutation 4: volatility normalisation wrapper
    mutations.append(
        f"({formula}) / (ts_std_dev(returns, 20) + 0.001)"
    )

    return mutations[:n]


# ── Startup / cleanup ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import atexit

    def _cleanup():
        global _auto_instance
        if _auto_instance:
            logging.info("Cleaning up browser instance…")
            _auto_instance.stop()

    atexit.register(_cleanup)

    logging.info("Starting Alpha Generator MCP Server…")
    logging.info("Tip: Agent should call get_skill_knowledge() at session start.")
    mcp.run()
