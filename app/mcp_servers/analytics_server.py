
from __future__ import annotations
import argparse
from typing import List

from mcp.server.fastmcp import FastMCP

from app.tools.analytics import analyse_quotes_request
from app.tools.models.analytics_model import Analytics
from app.tools.models.flight_search_model import Quote

mcp = FastMCP("AnalyticsTools")


@mcp.tool(name="analyse_quotes",
          description="Return price stats & histogram for a list of quotes")
def analyse_quotes(quotes: List[Quote]) -> Analytics:  
    return analyse_quotes_request(quotes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sse", action="store_true",
                        help="Run as an HTTP SSE server on port 8002")
    args = parser.parse_args()

    if args.sse:
        mcp.run(transport="sse", host="0.0.0.0", port=8002)
    else:
        mcp.run(transport="stdio")
