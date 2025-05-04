"""
Flight Search Agent Runner

This module provides a simple interface for executing the flight search agent.
It handles the execution of the agent and provides proper error handling.
"""

import asyncio
import logging
from typing import Dict, Any

from app.agent.client import get_client
from app.agent.graph import build_agent
from app.agent.state import GraphState

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def run_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the flight search agent with the given payload.
    
    Args:
        payload: Flight search parameters containing:
            - origin: 3-letter airport code
            - destination: 3-letter airport code
            - num_adults: number of adult passengers
            - departure_date: date in YYYY-MM-DD format
            
    Returns:
        Dict containing the search results
    """
    try:
        # Initialize state
        init_state = GraphState(
            origin=payload['origin'].upper(),
            destination=payload['destination'].upper(),
            num_adults=payload.get('num_adults', 1),
            departure_date=payload['departure_date'],
        )

        # Execute agent
        async with get_client() as client:
            agent = await build_agent(client)
            result = await agent.ainvoke(init_state, config={"callbacks": []})
            
            return {
                "quotes": result.get("quotes"),
                "aggregated_quotes": result.get("agg_quotes"),
                "screenshots": result.get("screenshots"),
                "analytics": result.get("analytics"),
            }
            
    except Exception as e:
        log.error("Flight search failed: %s", str(e), exc_info=True)
        raise

# async def main():
#     """Demo function to test the flight search agent."""
#     sample_request = {
#         "origin": "LHR",
#         "destination": "JFK",
#         "num_adults": 1,
#         "departure_date": "2025-06-01",
#     }
    
#     try:
#         result = await run_agent(sample_request)
#         print("Flight search result ⤵︎\n", result)
#     except Exception as e:
#         print(f"Error: {str(e)}")

# if __name__ == "__main__":
#     asyncio.run(main()) 