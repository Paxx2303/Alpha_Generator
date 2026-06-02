import json
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from wqb_automation import WQBAutomation, load_config
from alpha_agent import diagnose

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
def read_knowledge_base() -> str:
    """Read the Alpha generation knowledge base (Skill.md) containing themes, operators, and guidelines."""
    try:
        skill_path = Path("alpha_skills/Skill.md")
        if skill_path.exists():
            with open(skill_path, "r", encoding="utf-8") as f:
                return f.read()
        return "Skill.md not found."
    except Exception as e:
        return f"Error reading knowledge base: {e}"

@mcp.tool()
def submit_alpha(formula: str, universe: str = "TOP3000", neutralization: str = "Market", decay: int = 0, truncation: float = 0.05) -> str:
    """
    Submit a quantitative alpha formula to WorldQuant Brain for simulation.
    
    Args:
        formula: The alpha formula string using valid WQB operators.
        universe: Data universe (e.g. TOP200, TOP500, TOP1000, TOP3000). Default is TOP3000.
        neutralization: Type of neutralization (e.g. None, Market, Sector, Industry, Subindustry). Default is Market.
        decay: Number of days for linear decay (e.g. 0, 3, 5, 10, 20). Default is 0.
        truncation: Truncation threshold (e.g. 0.01, 0.05, 0.10). Default is 0.05.
        
    Returns:
        A JSON string containing the simulation results (Sharpe, Fitness, Turnover, Drawdown, etc.) or error message.
    """
    try:
        auto = get_automation()
        settings_str = f"{universe}|{neutralization}|{decay}|{truncation}"
        logging.info(f"Submitting formula: {formula} with settings: {settings_str}")
        
        result = auto.submit_alpha(formula, settings_str)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def diagnose_metrics(metrics_json: str) -> str:
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
def save_gold_alpha(formula: str, universe: str, neutralization: str, decay: int, truncation: float, metrics_json: str) -> str:
    """
    Save a successful alpha to the gold_alphas.json knowledge base.
    
    Args:
        formula: The alpha formula string.
        universe: Data universe used.
        neutralization: Type of neutralization used.
        decay: Linear decay value.
        truncation: Truncation value.
        metrics_json: The JSON string returned by submit_alpha.
        
    Returns:
        Success message.
    """
    try:
        metrics = json.loads(metrics_json)
        settings = {
            "universe": universe,
            "neutralization": neutralization,
            "decay": decay,
            "truncation": truncation
        }
        
        from alpha_agent import _save_gold_alpha
        import datetime
        
        entry = {
            "theme": "mcp_generated",
            "formula": formula,
            "settings": settings,
            "timestamp": str(datetime.datetime.now())
        }
        
        _save_gold_alpha(entry, metrics)
        return "Alpha saved successfully."
    except Exception as e:
        return f"Error saving alpha: {e}"

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
