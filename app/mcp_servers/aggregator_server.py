from __future__ import annotations
from typing import List
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AggregatorTools")

@mcp.tool(
    name="aggregate_quotes",
    description="Summarise a list of flight quotes (GBP)."
)
def aggregate_quotes(quotes: List[dict]) -> dict:
    # TODO: Implement the logic to aggregate the quotes
    return {"cheapest": min(q["price"] for q in quotes)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
