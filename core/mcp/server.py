"""
core/mcp/server.py — Alpha Generator MCP Server.

Transport: SSE on port 8765 (set via MCP_TRANSPORT=sse env var in vm-setup.sh).
DeerFlow connects via extensions_config.json:
  {"type": "sse", "url": "http://host.docker.internal:8765/sse"}

Fallback: MCP_TRANSPORT=stdio for local testing without Docker.
"""
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.mcp.tools.alpha import (
    submit_alpha,
    get_gold_alphas,
    diagnose_alpha,
    mutate_formula,
)
from core.mcp.tools.memory import (
    update_skill,
    save_theory,
)
from core.mcp.tools.research import (
    search_data_fields,
    get_skill_knowledge,
)

logging.basicConfig(level=logging.INFO, stream=sys.stderr)

mcp = FastMCP("Alpha Generator Server")

# Register tools
mcp.tool()(submit_alpha)
mcp.tool()(get_gold_alphas)
mcp.tool()(diagnose_alpha)
mcp.tool()(mutate_formula)
mcp.tool()(update_skill)
mcp.tool()(save_theory)
mcp.tool()(search_data_fields)
mcp.tool()(get_skill_knowledge)

if __name__ == "__main__":
    import os
    import atexit
    from core.mcp.tools.alpha import _cleanup_automation
    atexit.register(_cleanup_automation)

    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        port = int(os.getenv("MCP_PORT", "8765"))
        logging.info(f"Starting Alpha Generator MCP Server (SSE port {port})…")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        logging.info("Starting Alpha Generator MCP Server (stdio)…")
        mcp.run()
