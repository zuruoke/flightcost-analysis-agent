from __future__ import annotations
import argparse
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FlightTools")

@mcp.tool(
    name="flight_search",
    description="Return three cheapest one-way economy flights (GBP)"
)
async def flight_search(
    origin: str,
    destination: str,
    number_of_adults: int = 1,
    departure_date: Optional[str] = None,
) -> List[dict]:
    # TODO: Implement the logic to search for flights
    return [
        {"price": 100, "deep_link": "http://a.com"},
        {"price": 120, "deep_link": "http://b.com"},
        {"price": 140, "deep_link": "http://c.com"},
    ]

if __name__ == "__main__":
    mcp.run(transport="stdio")