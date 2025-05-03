"""
graph.py – Build and compile the LangGraph DAG.

• Discovers tools from four separate FastMCP servers via MultiServerMCPClient
  (flight_search, aggregator, screenshot, analytics).
• Keeps the router LLM schema-guarded and retry-safe.
• Exposes the compiled graph as ``flight_agent``.
"""

from __future__ import annotations
import asyncio
import logging
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info("Discovering tools from MCP servers...")
    async with MultiServerMCPClient(SERVER_CFG) as client:
        tools = client.get_tools()
        def _alias(t: StructuredTool) -> str:
            return t.name.split("/", 1)[1] if "/" in t.name else t.name
        tool_map = {_alias(t): t for t in tools}
        logger.info(f"Discovered {len(tool_map)} tools: {list(tool_map.keys())}")
        return tool_map

# Initialize tool map
tool_map: Dict[str, StructuredTool] = {}

async def initialize_tools():
    """Initialize the tool map."""
    global tool_map
    logger.info("Initializing tools...")
    tool_map = await get_tool_map()
    logger.info("Tools initialization complete")

# Run the initialization
logger.info("Starting tool initialization...")
asyncio.run(initialize_tools())

# Aliases for clarity
t_flight = tool_map["flight_search"]
t_agg    = tool_map["aggregate_quotes"]
t_shot   = tool_map["screenshot_data"]
t_stats  = tool_map["analyse_quotes"]

# ───────────────────────────── Router LLM node ─────────────────────────────
parser     = PydanticOutputParser(pydantic_object=RouterDecision)
router_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0,
    model_kwargs={
        "messages": [
            {"role": "system", "content": ROUTER_PROMPT + parser.get_format_instructions()}
        ]
    }
)

def router(state: GraphState) -> dict:
    """Return the next tool name and arguments. Retries once on schema error, then falls back."""
    logger.info(f"Router received state: {state.model_dump_json(indent=2)}")
    
    for attempt in range(1 + MAX_ROUTER_RETRIES):
        logger.info(f"Router attempt {attempt + 1}/{1 + MAX_ROUTER_RETRIES}")
        # Format the state as a proper message
        state_message = f"Current state:\n{state.model_dump_json(indent=2)}"
        logger.debug(f"Sending to router LLM: {state_message}")
        
        try:
            # Get the raw response from the LLM
            response = router_llm.invoke(state_message)
            logger.debug(f"Router LLM raw response: {response}")
            
            # Extract content from AIMessage
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Clean the content to ensure it's valid JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            logger.debug(f"Cleaned content: {content}")
            
            try:
                # Parse the content into a RouterDecision
                decision = parser.parse(content)
                logger.info(f"Router decision: {decision.tool_name}")
                return {"tool_name": decision.tool_name, "tool_args": decision.tool_args}
            except Exception as parse_error:
                logger.warning(f"Failed to parse content as JSON: {str(parse_error)}")
                logger.warning(f"Content was: {content}")
                continue
                
        except Exception as e:
            logger.warning(f"Router attempt {attempt + 1} failed: {str(e)}")
            continue
    
    # deterministic fallback
    logger.info("Using deterministic fallback routing")
    if not state.quotes:
        logger.info("No quotes found, routing to flight_search_tool")
        return {"tool_name": "flight_search_tool", "tool_args": {}}
    if not state.agg_quotes:
        logger.info("No aggregated quotes found, routing to aggregator_tool")
        return {"tool_name": "aggregator_tool", "tool_args": {}}
    if not state.screenshots:
        logger.info("No screenshots found, routing to screenshot_tool")
        return {"tool_name": "screenshot_tool", "tool_args": {}}
    if not state.analytics:
        logger.info("No analytics found, routing to analytics_tool")
        return {"tool_name": "analytics_tool", "tool_args": {}}
    logger.info("All data present, routing to response_builder")
    return {"tool_name": "response_builder", "tool_args": {}}

# ─────────────────────────── Response-builder LLM ───────────────────────────
answer_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    model_kwargs={
        "messages": [
            {"role": "system", "content": (
                "You are a friendly travel concierge. "
                "Return markdown with:\n"
                "• summary paragraph\n• table of 5 cheapest quotes\n• <img> tags for screenshots"
            )}
        ]
    }
)

# ──────────────────────────────── Build DAG ────────────────────────────────
logger.info("Building LangGraph DAG...")
memory = MemorySaver()
g = StateGraph(GraphState)

# Add nodes
logger.info("Adding nodes to graph...")
g.add_node("router",          router)
g.add_node("flight_search",   t_flight)
g.add_node("aggregate_quotes",       t_agg)
g.add_node("screenshot_data",      t_shot)
g.add_node("analyse_quotes",       t_stats)
g.add_node("response_builder", answer_llm)

# Add edges
logger.info("Adding edges to graph...")
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
logger.info("LangGraph DAG compilation complete")

__all__ = ["flight_agent"]
