from __future__ import annotations
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from app.tools.flight_search import flight_search_request
from app.tools.models.flight_search_model import Quote


mcp = FastMCP("FlightTools")

# ──────────────────────────── MCP flight_search tool ────────────────────────
@mcp.tool(name="flight_search",
          description=(
              "Search for the three cheapest one-way economy flights. "
              "Dates are YYYY-MM-DD. Currency is GBP."
          ))
async def flight_search(
    origin: str,
    destination: str,
    number_of_adults: int = 1,
    departure_date: Optional[str] = None,
)-> List[Quote]:
    """
    Return a list of ``Quote`` objects. All prices are in GBP.
    """
    return await flight_search_request(
        origin=origin, 
        departure_date=departure_date, 
        destination=destination, 
        number_of_adults=number_of_adults
    )



# ──────────────────────────── CLI entry point ───────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sse", action="store_true",
                        help="Run as an HTTP SSE server on port 8000 "
                             "(instead of the default stdio transport).")
    args = parser.parse_args()

    if args.sse:
        mcp.run(transport="sse", host="0.0.0.0", port=8000)
    else:
        mcp.run(transport="stdio")
