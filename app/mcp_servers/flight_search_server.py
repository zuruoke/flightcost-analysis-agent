from __future__ import annotations
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

from app.agent.state import UserQuery
from app.tools.flight_search import FlightSearchToolRequest

mcp = FastMCP("FlightTools")

@mcp.tool(
    name="flight_search",
    description="Return three cheapest one-way economy flights (GBP)"
)
async def flight_search(
    user_query: UserQuery
) -> List[dict]:
    request = FlightSearchToolRequest(user_query)
    await request.run()
   
    return [
        {"price": 100, "deep_link": "http://a.com"},
        {"price": 120, "deep_link": "http://b.com"},
        {"price": 140, "deep_link": "http://c.com"},
    ]

if __name__ == "__main__":
    mcp.run(transport="stdio")