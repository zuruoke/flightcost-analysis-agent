from __future__ import annotations
from typing import List
from mcp.server.fastmcp import FastMCP
from app.tools.aggregator import aggregate_quotes_request
from app.tools.models.aggregator_model import Aggregation
from app.tools.models.flight_search_model import Quote

# ───────────────────────────── FastMCP server ───────────────────────────────
mcp = FastMCP("AggregatorTools")


@mcp.tool(name="aggregate_quotes",
          description="Summarise a list of flight quotes (GBP).")
def aggregate_quotes(quotes: List[Quote]) -> Aggregation:
    return aggregate_quotes_request(quotes)


# ─────────────────────────── CLI entry point ────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sse", action="store_true",
                        help="Run as an HTTP SSE server on port 8001")
    args = parser.parse_args()

    if args.sse:
        mcp.run(transport="sse", host="0.0.0.0", port=8001)
    else:
        mcp.run(transport="stdio")
