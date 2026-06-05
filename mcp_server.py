import json
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import datetime

from wqb_automation import WQBAutomation, load_config

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
def get_skill_knowledge() -> str:
    """
    Get the comprehensive skill knowledge base (mcp_skill.md) containing:
    - MCP tools documentation and capabilities
    - Core knowledge and rules for alpha generation
    - Valid operators and broken operators to avoid
    - Advanced optimization techniques
    - Proven settings grid
    - Examples of high-quality composite alphas
    
    IMPORTANT: Call this tool at the start of your session to load domain knowledge!
    """
    try:
        skill_file = Path(__file__).parent / "mcp_skill.md"
        if skill_file.exists():
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        else:
            return "Error: mcp_skill.md not found"
    except Exception as e:
        return f"Error reading skill file: {str(e)}"

@mcp.tool()
def search_data_fields(query: str, limit: int = 20) -> list:
    """
    Search WorldQuant Brain's API for available data fields like fundamentals, sentiment, estimates, etc.
    Use this to discover real variables you can use in your alpha formulas.
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
    """
    try:
        import sys
        from pathlib import Path
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

# TODO: diagnose_alpha tool — chưa implement
# Kế hoạch: Thêm hàm để phân tích metrics của alpha và đưa ra khuyến nghị sửa lỗi
# (VD: "HIGH_TURNOVER -> Increase Decay", "LOW_SHARPE -> Change neutralization")

if __name__ == "__main__":
    import atexit
    
    def cleanup():
        global _auto_instance
        if _auto_instance:
            logging.info("Cleaning up browser instance...")
            _auto_instance.stop()
            
    atexit.register(cleanup)
    
    logging.info("Starting Alpha Generator MCP Server...")
    logging.info("IMPORTANT: Agent should call get_skill_knowledge() at startup to load domain knowledge!")
    mcp.run()
