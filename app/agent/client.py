"""
Utility that spins-up four MCP servers via STDIO and
exposes a single MultiServerMCPClient whose .get_tools()
works exactly like in the README.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient


ROOT = Path(__file__).resolve().parent.parent / "mcp_servers"

SERVER_CFG = {
    "flight": {
        "command": "python",
        "args": [str(ROOT / "flight_search_server.py")],
        "transport": "stdio",
    },
    "aggregator": {
        "command": "python",
        "args": [str(ROOT / "aggregator_server.py")],
        "transport": "stdio",
    },
    "analytics": {
        "command": "python",
        "args": [str(ROOT / "analytics_server.py")],
        "transport": "stdio",
    },
    "screenshot": {
        "command": "python",
        "args": [str(ROOT / "screenshot_server.py")],
        "transport": "stdio",
    },
}

@asynccontextmanager
async def get_client():
    async with MultiServerMCPClient(SERVER_CFG) as client:
        yield client
