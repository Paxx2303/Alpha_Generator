import json
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import datetime

from wqb_automation import WQBAutomation, load_config
from alpha_agent import (
    diagnose, 
    _save_gold_alpha, 
    get_next_hypothesis, 
    mutate_formula,
    THEMES
)

logging.basicConfig(level=logging.INFO)

# Create an MCP server
mcp = FastMCP("Alpha Generator Server")

# Global variables for long-running automation instance
_auto_instance = None
_is_logged_in = False

def get_automation() -> WQBAutomation:
    global _auto_instance, _is_logged_in
    if _auto_instance is None:
        logging.info("Initializing WQBAutomation...")
        config = load_config()
        # Ensure we run headless by default for the MCP server so it doesn't interrupt the user
        config["headless"] = True
        
        _auto_instance = WQBAutomation(config)
        _auto_instance.start()
        
    if not _is_logged_in:
        logging.info("Logging into WorldQuant Brain...")
        _is_logged_in = _auto_instance.login()
        if not _is_logged_in:
            logging.error("Failed to login to WorldQuant Brain")
            
    return _auto_instance

@mcp.tool()
def generate_hypothesis(theme: str = None, avoid_themes: list = None) -> dict:
    """
    Generate a new alpha hypothesis based on the knowledge base.
    
    Args:
        theme: Specify a particular theme to generate a hypothesis for.
        avoid_themes: List of themes to avoid.
    """
    try:
        if avoid_themes is None:
            avoid_themes = []
            
        if theme and theme in THEMES:
            from alpha_agent import generate_variants
            theme_dict = THEMES[theme]
            variants = generate_variants(theme, theme_dict, [])
            return {
                "theme": theme,
                "name": theme_dict["name"],
                "rationale": theme_dict["rationale"],
                "variants": variants,
                "settings": dict(theme_dict["settings"])
            }
            
        hyp = get_next_hypothesis([], avoid_themes)
        if hyp:
            return hyp
        return {"error": "No hypotheses could be generated."}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def search_data_fields(query: str, limit: int = 20) -> list:
    """
    Search WorldQuant Brain's API for available data fields like fundamentals, sentiment, estimates, etc.
    Use this to discover real variables you can use in your alpha formulas.
    
    Args:
        query: The search string (e.g. 'sales', 'sentiment', 'options', 'implied volatility')
        limit: Number of results to return (max 50, default 20)
    """
    try:
        auto = get_automation()
        results = auto.search_data_fields(query, limit)
        return results
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Search the internal knowledge base (JSON datasets and markdown papers) for alpha theories, economic rationales, and trading ideas.
    ALWAYS use this tool before generating a new theme or hypothesis to ground it in academic research.
    
    Args:
        query: The search string (e.g. 'momentum', 'mean reversion', 'earnings announcement', 'liquidity')
        top_k: Number of top results to return.
    """
    try:
        import sys
        from pathlib import Path
        # Ensure alpha_skills is in path so we can import knowledge_retriever
        skills_path = str(Path(__file__).parent / "alpha_skills")
        if skills_path not in sys.path:
            sys.path.append(skills_path)
            
        from knowledge_retriever import KnowledgeRetriever
        retriever = KnowledgeRetriever()
        return retriever.search(query, top_k)
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"

@mcp.tool()
def submit_alpha(formula: str, settings: dict = None, dry_run: bool = True) -> str:
    """
    Submit a quantitative alpha formula to WorldQuant Brain for simulation.
    
    Args:
        formula: The alpha formula string using valid WQB operators.
        settings: A dictionary of settings e.g. {"universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05}
        dry_run: If True, will not submit to the live API. Default is True for safety.
        
    Returns:
        A JSON string containing the simulation results or error message.
    """
    if dry_run:
        return json.dumps({
            "message": "Dry-run mode is active. No submission made.",
            "formula": formula,
            "settings": settings,
        }, indent=2)

    try:
        auto = get_automation()
        if not settings:
            settings = {"universe": "TOP3000", "neutralization": "Market", "decay": 0, "truncation": 0.05}
            
        settings_str = f"{settings.get('universe', 'TOP3000')}|{settings.get('neutralization', 'Market')}|{settings.get('decay', 0)}|{settings.get('truncation', 0.05)}"
        logging.info(f"Submitting formula: {formula} with settings: {settings_str}")
        
        result = auto.submit_alpha(formula, settings_str)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def diagnose_alpha(metrics_json: str) -> str:
    """
    Diagnose simulation results to find issues and suggest fixes.
    
    Args:
        metrics_json: The JSON string returned by submit_alpha containing metrics like sharpe, fitness, turnover.
        
    Returns:
        A JSON string containing a list of diagnosis issues and suggested fixes.
    """
    try:
        metrics = json.loads(metrics_json)
        diagnoses = diagnose(metrics)
        return json.dumps(diagnoses, indent=2)
    except Exception as e:
        return json.dumps([{"issue": "JSON_PARSE_ERROR", "fix": str(e), "priority": 1}])

@mcp.tool()
def list_gold_alphas(limit: int = 20, min_sharpe: float = 0.0) -> list:
    """
    List successfully discovered gold alphas from the local knowledge base.
    
    Args:
        limit: Max number of alphas to return.
        min_sharpe: Minimum sharpe ratio to filter by.
    """
    try:
        path = Path("wqb_logs/gold_alphas.json")
        if not path.exists():
            return []
            
        with open(path) as f:
            data = json.load(f)
            
        filtered = [a for a in data if a.get("score", 0) >= min_sharpe]
        filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
        return filtered[:limit]
    except Exception as e:
        logging.error(f"Failed to list gold alphas: {e}")
        return []

@mcp.tool()
def mutate_from_gold(base_formula: str = None, n: int = 5) -> list:
    """
    Generate mutations for an existing formula.
    
    Args:
        base_formula: The alpha formula to mutate. If None, it will pick the best gold alpha.
        n: Number of mutated variants to return.
    """
    if base_formula is None:
        golds = list_gold_alphas(limit=1)
        if not golds:
            return ["No gold alphas found to mutate."]
        base_formula = golds[0]["formula"]
        
    return mutate_formula(base_formula, n=n)


if __name__ == "__main__":
    import atexit
    
    def cleanup():
        global _auto_instance
        if _auto_instance:
            logging.info("Cleaning up browser instance...")
            _auto_instance.stop()
            
    atexit.register(cleanup)
    
    logging.info("Starting Alpha Generator MCP Server...")
    mcp.run()
