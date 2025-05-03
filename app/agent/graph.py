"""
graph.py – Build and compile the LangGraph DAG.

• Discovers tools from four separate FastMCP servers via MultiServerMCPClient
  (flight_search, aggregator, screenshot, analytics).
• Keeps the router LLM schema-guarded and retry-safe.
• Exposes the compiled graph as ``flight_agent``.
"""

from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from typing import Dict
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.callbacks.base import BaseCallbackHandler

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools import StructuredTool

from agent.state import GraphState
from agent.router_schema import RouterDecision
from agent.router_prompt import PROMPT
from agent.constants import MAX_ROUTER_RETRIES

# ────────────────────────────── MCP discovery ──────────────────────────────
SERVER_CFG = {
    # Each server lives in its own container / VM / process
    "flighttools": {
        "url": "http://flighttools:7000/sse",
        "transport": "sse",
    },
    "aggregatortools": {
        "url": "http://aggregatortools:7001/sse",
        "transport": "sse",
    },
    "screenshottools": {
        "url": "http://screenshottools:7002/sse",
        "transport": "sse",
    },
    "analyticstools": {
        "url": "http://analyticstools:7003/sse",
        "transport": "sse",
    },
}


@asynccontextmanager
async def discover_tool_map() -> Dict[str, StructuredTool]:
    """
    Connect to every MCP server in ``SERVER_CFG`` and yield a {name: tool} map.
    We strip the automatic ``server/`` prefix so downstream code can reference
    tools exactly as before: ``flight_search``, ``aggregator``, …
    """
    async with MultiServerMCPClient(SERVER_CFG) as client:
        tools = client.get_tools()                       # flattened list
        def _alias(t: StructuredTool) -> str:            # strip "<server>/"
            return t.name.split("/", 1)[1] if "/" in t.name else t.name
        yield {_alias(t): t for t in tools}


# LangGraph builds its DAG at import-time → synchronously pull tools once.
tool_cm = discover_tool_map()
tool_map: Dict[str, StructuredTool] = asyncio.run(tool_cm.__aenter__())

# Aliases for clarity
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
memory = MemorySaver()
g = StateGraph(GraphState)

g.add_node("router",          router)
g.add_node("flight_search",   t_flight)
g.add_node("aggregate",       t_agg)
g.add_node("screenshot",      t_shot)
g.add_node("analytics",       t_stats)
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

# after crafting the final answer we end the run
g.add_edge("response_builder", END)

flight_agent = g.compile(checkpointer=memory)

# ───────────────────────── cleanup after import ────────────────────────────
asyncio.run(tool_cm.__aexit__(None, None, None))

__all__ = ["flight_agent"]
