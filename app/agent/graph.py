from pathlib import Path
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from agent.manifest_loader import load_tool_from_manifest

from agent.state import GraphState
from agent.router_prompt import ROUTER_PROMPT
from agent.router_schema import RouterDecision
from agent.constants import MAX_ROUTER_RETRIES

# ──────────────────────────── load MCP tools ────────────────────────────
MANIFEST_DIR = Path(__file__).parent.parent / "tools" / "manifests"
load = lambda n: load_tool_from_manifest(MANIFEST_DIR / f"{n}.yaml")

t_flight = load("flight_search")
t_agg    = load("aggregator")
t_shot   = load("screenshot")
t_stats  = load("analytics")

# ─────────────────────── router LLM + schema guard ──────────────────────
parser      = PydanticOutputParser(pydantic_object=RouterDecision)
router_llm  = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    system=ROUTER_PROMPT + parser.get_format_instructions(),
)

def router(state: GraphState) -> str:
    """
    Ask the LLM for next tool; schema-validate; retry on failure;
    fall back to deterministic logic on last resort.
    """
    for attempt in range(1 + MAX_ROUTER_RETRIES):
        raw = router_llm.invoke({"state_json": state.model_dump_json()})
        try:
            decision = parser.parse(raw)
            return decision.tool_name
        except Exception as exc:           
            if attempt == MAX_ROUTER_RETRIES:
                
                if not state.quotes:
                    return "flight_search_tool"
                if not state.agg_quotes:
                    return "aggregator_tool"
                if not state.screenshots:
                    return "screenshot_tool"
                if not state.analytics:
                    return "analytics_tool"
                return "response_builder"

# ───────────────────────── response builder LLM ─────────────────────────
answer_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    system=(
        "You are a friendly travel concierge. Produce markdown containing:\n"
        "• A short price summary\n"
        "• A table of the 5 cheapest itineraries (price, airline, link)\n"
        "• <img> tags for every screenshot URL in state.screenshots."
    ),
)

# ───────────────────────────── build the DAG ────────────────────────────
g = StateGraph(GraphState)

# Nodes
g.add_node("router",       router)
g.add_node("flight_search",t_flight)
g.add_node("aggregate",    t_agg)
g.add_node("screenshot",   t_shot)
g.add_node("analytics",    t_stats)
g.add_node("response_builder", answer_llm)

# Router → next-tool edges
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

# Deterministic nodes loop back to router
for name in ["flight_search", "aggregate", "screenshot", "analytics"]:
    g.add_edge(name, "router")

# After the answer LLM, we’re done
g.add_edge("response_builder", END)

flight_agent = g.compile()     # ← import-time, thread-safe
