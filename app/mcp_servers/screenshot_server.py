from __future__ import annotations
import argparse
from typing import List
from mcp.server.fastmcp import FastMCP
from app.tools.models.screenshot_model import ScreenshotRequest, ScreenshotResult
from app.tools.screenshot import take_screenshots




mcp = FastMCP("ScreenshotTools")


@mcp.tool(name="screenshot_data",
          description="Return S3 image URLs for a list of page URLs")
async def screenshot_data(
    reqs: List[ScreenshotRequest],
) -> List[ScreenshotResult]:
    return await take_screenshots(reqs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sse", action="store_true",
                        help="Run as an HTTP SSE server on port 8003")
    args = parser.parse_args()

    if args.sse:
        mcp.run(transport="sse", host="0.0.0.0", port=8003)
    else:
        mcp.run(transport="stdio")
