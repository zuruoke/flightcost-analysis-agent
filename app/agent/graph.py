"""
Flight Search Agent Graph Builder

This module implements a LangGraph-based flight search agent that:
1. Searches for flights based on user criteria
2. Aggregates flight quotes
3. Captures screenshots of flight details
4. Analyzes flight statistics
5. Returns comprehensive flight search results

The agent uses a directed acyclic graph (DAG) to orchestrate the workflow,
with each node representing a specific task in the flight search process.
"""

from __future__ import annotations
import logging
from typing import Dict

from langgraph.graph import StateGraph, START, END
from langchain_core.tools import StructuredTool

from app.agent.state import GraphState
from app.agent.tracing import trace, _as_python

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def build_agent(client):
    """
    Build and compile the flight search agent graph.
    
    This function:
    1. Discovers and maps available MCP tools
    2. Defines the routing logic for the workflow
    3. Creates async wrappers for each tool
    4. Constructs and compiles the DAG
    
    Args:
        client: The MCP client instance
        
    Returns:
        StateGraph: A compiled LangGraph instance ready for execution
    """
    # 1. Discover and map MCP tools
    tool_map: Dict[str, StructuredTool] = {
        t.name.split("/", 1)[-1]: t for t in client.get_tools()
    }
    t_flight = tool_map["flight_search"]
    t_agg = tool_map["aggregate_quotes"]
    t_shot = tool_map["screenshot_data"]
    t_stats = tool_map["analyse_quotes"]

    # 2. Define routing logic
    @trace("decide")
    def decide(s: GraphState) -> str:
        """
        Determine the next node in the workflow based on current state.
        
        The workflow follows this sequence:
        1. flight_search -> 2. aggregate_quotes -> 3. screenshot_data -> 4. analyse_quotes
        
        Args:
            s (GraphState): Current state of the workflow
            
        Returns:
            str: Name of the next node to execute
        """
        if s.quotes is None: return "flight"
        if s.agg_quotes is None: return "agg"
        if s.screenshots is None: return "shot"
        if s.analytics is None: return "stats"
        return "finish"

    @trace("router")
    def router(_: GraphState) -> dict:
        """Empty router function that returns an empty dict."""
        return {}

    # 3. Create async wrappers for each tool
    @trace("flight")
    async def flight(s: GraphState):
        """
        Search for flights based on user criteria.
        
        Args:
            s (GraphState): State containing search parameters
            
        Returns:
            dict: Flight quotes
        """
        raw = await t_flight.ainvoke({
            "origin": s.origin,
            "destination": s.destination,
            "number_of_adults": s.num_adults,
            "departure_date": s.departure_date,
        })
        return {"quotes": _as_python(raw)}

    @trace("agg")
    async def agg(s: GraphState):
        """
        Aggregate flight quotes into a summary.
        
        Args:
            s (GraphState): State containing flight quotes
            
        Returns:
            dict: Aggregated flight quotes
        """
        summary = await t_agg.ainvoke({"quotes": s.quotes})
        return {"agg_quotes": _as_python(summary)}

    @trace("shot")
    async def shot(s: GraphState):
        """
        Capture screenshots of flight details.
        
        Args:
            s (GraphState): State containing flight quotes with deep links
            
        Returns:
            dict: URLs of captured screenshots
        """
        urls = await t_shot.ainvoke(
            {"reqs": [q["deep_link"] for q in s.quotes]}
        )
        return {"screenshots": _as_python(urls)}

    @trace("stats")
    async def stats(s: GraphState):
        """
        Analyze flight quotes for statistics.
        
        Args:
            s (GraphState): State containing flight quotes
            
        Returns:
            dict: Flight statistics and analytics
        """
        ana = await t_stats.ainvoke({"quotes": s.quotes})
        return {"analytics": _as_python(ana)}

    # 4. Construct and compile the DAG
    g = StateGraph(GraphState)
    
    # Add nodes
    g.add_node("router", router)
    g.add_node("flight", flight)
    g.add_node("agg", agg)
    g.add_node("shot", shot)
    g.add_node("stats", stats)

    # Add edges
    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router", decide,
        path_map={
            "flight": "flight",
            "agg": "agg",
            "shot": "shot",
            "stats": "stats",
            "finish": END,
        },
    )
    
    # Connect all nodes back to router
    for n in ("flight", "agg", "shot", "stats"):
        g.add_edge(n, "router")

    # Compile the graph
    compiled = g.compile()
    log.info("✈️  LangGraph compiled with %s nodes", len(compiled.nodes))
    return compiled
