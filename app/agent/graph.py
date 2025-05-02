"""
Build and compile the LangGraph DAG.

• Discovers all tools from the “FlightTools” FastMCP server (tools container)
  via MultiServerMCPClient + SSE.
• Keeps the router LLM schema-guarded and retry-safe.
• Exposes the compiled graph as `flight_agent`.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.tools import StructuredTool

from agent.state import GraphState
from agent.router_schema import RouterDecision
from agent.router_prompt import PROMPT
from agent.constants import ALLOWED_TOOL_NAMES, MAX_ROUTER_RETRIES


# ────────────────────────────── MCP discovery ──────────────────────────────
TOOLS_SSE_URL = "http://tools:7000/sse"    


@asynccontextmanager
async def discover_tool_map() -> Dict[str, StructuredTool]:
    """
    Connect to one (or many) MCP servers and yield a {name: tool} mapping.
    We wrap it in a context-manager so the network session is gracefully closed
    once the graph has loaded the tools.
    """
    async with MultiServerMCPClient(
        {
            "flighttools": {
                "url": TOOLS_SSE_URL,
                "transport": "sse",
            }
        }
    ) as client:
        tools = await load_mcp_tools(client.session)      # list[StructuredTool]
        yield {t.name: t for t in tools}


# Because LangGraph builds the DAG at import-time we synchronously pull the tools
# once.  If you prefer non-blocking startup, move this call into a FastAPI
# startup event and rebuild the graph there.
tool_map: Dict[str, StructuredTool]
tool_cm = discover_tool_map()
tool_map = asyncio.run(tool_cm.__aenter__())      # noqa: E402  (top-level)

# Alias for clarity
t_flight = tool_map["flight_search"]
t_agg    = tool_map["aggregator"]
t_shot   = tool_map["screenshot"]
t_stats  = tool_map["analytics"]

# ───────────────────────────── Router LLM node ─────────────────────────────
parser     = PydanticOutputParser(pydantic_object=RouterDecision)
router_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    system=PROMPT + parser.get_format_instructions(),
)

def router(state: GraphState) -> str:
    """Return the next tool name. Retries once on schema error, then falls back."""
    for _ in range(1 + MAX_ROUTER_RETRIES):
        raw = router_llm.invoke({"state_json": state.model_dump_json()})
        try:
            return parser.parse(raw).tool_name
        except Exception:
            continue
    # deterministic fallback
    if not state.quotes:
        return "flight_search_tool"
    if not state.agg_quotes:
        return "aggregator_tool"
    if not state.screenshots:
        return "screenshot_tool"
    if not state.analytics:
        return "analytics_tool"
    return "response_builder"

# ─────────────────────────── Response-builder LLM ───────────────────────────
answer_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    system=(
        "You are a friendly travel concierge. "
        "Return markdown with:\n"
        "• summary paragraph\n• table of 5 cheapest quotes\n• <img> tags for screenshots"
    ),
)

# ──────────────────────────────── Build DAG ────────────────────────────────
g = StateGraph(GraphState)

g.add_node("router", router)
g.add_node("flight_search", t_flight)
g.add_node("aggregate",     t_agg)
g.add_node("screenshot",    t_shot)
g.add_node("analytics",     t_stats)
g.add_node("response_builder", answer_llm)

g.add_conditional_edges(
    "router",
    {
        "flight_search_tool": "flight_search",
        "aggregator_tool":    "aggregate",
        "screenshot_tool":    "screenshot",
        "analytics_tool":     "analytics",
        "response_builder":   "response_builder",
        "finish":             END,
    },
)

# deterministic tools loop back to router
for name in ("flight_search", "aggregate", "screenshot", "analytics"):
    g.add_edge(name, "router")

# after we craft the final answer we end the run
g.add_edge("response_builder", END)

flight_agent = g.compile()

# ───────────────────────── cleanup after import ────────────────────────────
# Close the client session now that the tools are loaded
asyncio.run(tool_cm.__aexit__(None, None, None))

__all__ = ["flight_agent"]
