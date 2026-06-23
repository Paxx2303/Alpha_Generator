# mcp_server.py — legacy entry point, delegates to core/mcp/server.py
# vm-setup.sh now launches core/mcp/server.py directly (SSE transport).
# This file is kept only for local stdio testing convenience.
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.mcp.server import mcp  # noqa: F401

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    logging.info("Starting Alpha Generator MCP Server (stdio via legacy entry point)…")
    mcp.run()
