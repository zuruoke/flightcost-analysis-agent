from __future__ import annotations
import argparse
from typing import List
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AnalyticsTools")

@mcp.tool(
    name="analyse_quotes",
    description="Return price stats & histogram for a list of quotes"
)
def analyse_quotes(quotes: List[dict]) -> dict:
    # TODO: Implement the logic to analyse the quotes
    return {"count": len(quotes), "name": "Zuruoke"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
