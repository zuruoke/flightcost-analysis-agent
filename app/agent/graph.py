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

from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools import StructuredTool

from app.agent.router_prompt import ROUTER_PROMPT
from app.agent.state import GraphState
from app.agent.router_schema import RouterDecision
from app.agent.constants import MAX_ROUTER_RETRIES

# ────────────────────────────── MCP discovery ──────────────────────────────
SERVER_CFG = {
    "flighttools": {
        "args": ["/Users/chimzuruokeokafor/cozn/travel-flight-agent/app/mcp_servers/flight_search_server.py"],
        "command": "python",
        "transport": "stdio",
    },
    "aggregatortools": {
        "args": ["/Users/chimzuruokeokafor/cozn/travel-flight-agent/app/mcp_servers/aggregator_server.py"],
        "command": "python",
    },
    "screenshottools": {
        "args": ["/Users/chimzuruokeokafor/cozn/travel-flight-agent/app/mcp_servers/screenshot_server.py"],
        "command": "python",
    },
    "analyticstools": {
        "args": ["/Users/chimzuruokeokafor/cozn/travel-flight-agent/app/mcp_servers/analytics_server.py"],
        "command": "python",
    },
}

async def get_tool_map() -> Dict[str, StructuredTool]:
    """Get the tool map by running the async context manager."""
    async with MultiServerMCPClient(SERVER_CFG) as client:
        tools = client.get_tools()
        def _alias(t: StructuredTool) -> str:
            return t.name.split("/", 1)[1] if "/" in t.name else t.name
        return {_alias(t): t for t in tools}

# Initialize tool map
tool_map: Dict[str, StructuredTool] = {}

async def initialize_tools():
    """Initialize the tool map."""
    global tool_map
    tool_map = await get_tool_map()

# Run the initialization
asyncio.run(initialize_tools())

# Aliases for clarity
t_flight = tool_map["flight_search"]
t_agg    = tool_map["aggregate_quotes"]
t_shot   = tool_map["screenshot_data"]
t_stats  = tool_map["analyse_quotes"]

# ───────────────────────────── Router LLM node ─────────────────────────────
parser     = PydanticOutputParser(pydantic_object=RouterDecision)
router_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    model_kwargs={
        "system": ROUTER_PROMPT + parser.get_format_instructions()
    }
)

def router(state: GraphState) -> RouterDecision:
    """Return the next tool name. Retries once on schema error, then falls back."""
    for _ in range(1 + MAX_ROUTER_RETRIES):
        raw = router_llm.invoke({"state_json": state.model_dump_json()})
        try:
            return parser.parse(raw)
        except Exception:
            continue
    # deterministic fallback
    if not state.quotes:
        return RouterDecision(tool_name="flight_search")
    if not state.agg_quotes:
        return RouterDecision(tool_name="aggregate_quotes")
    if not state.screenshots:
        return RouterDecision(tool_name="screenshot_data")
    if not state.analytics:
        return RouterDecision(tool_name="analyse_quotes")
    return RouterDecision(tool_name="response_builder")

# ─────────────────────────── Response-builder LLM ───────────────────────────
answer_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    model_kwargs={
        "system": (
            "You are a friendly travel concierge. "
            "Return markdown with:\n"
            "• summary paragraph\n• table of 5 cheapest quotes\n• <img> tags for screenshots"
        )
    }
)

# ──────────────────────────────── Build DAG ────────────────────────────────
memory = MemorySaver()
g = StateGraph(GraphState)

g.add_node("router",          router)
g.add_node("flight_search",   t_flight)
g.add_node("aggregate_quotes",       t_agg)
g.add_node("screenshot_data",      t_shot)
g.add_node("analyse_quotes",       t_stats)
g.add_node("response_builder", answer_llm)

g.add_edge(START, "router")

g.add_conditional_edges(
    "router",
    {
        "flight_search": lambda x: "flight_search",
        "aggregate_quotes": lambda x: "aggregate_quotes",
        "screenshot_data": lambda x: "screenshot_data",
        "analyse_quotes": lambda x: "analyse_quotes",
        "response_builder": lambda x: "response_builder",
        "finish": lambda x: END,
    },
)

# deterministic tools loop back to router
for name in ("flight_search", "aggregate_quotes", "screenshot_data", "analyse_quotes"):
    g.add_edge(name, "router")

# after crafting the final answer we end the run
g.add_edge("response_builder", END)

flight_agent = g.compile(checkpointer=memory)

__all__ = ["flight_agent"]
