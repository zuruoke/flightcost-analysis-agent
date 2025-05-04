from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List
import os
import httpx
import logging
from app.agent.state import UserQuery
from app.tools.models.flight_search_model import Quote, Segment

# Set up logging
logger = logging.getLogger(__name__)

KIWI_API   = "https://api.tequila.kiwi.com/v2/search"
CURRENCY   = "GBP"
API_KEY    = "FENuirN6cHfnRL2Vu2cxVWEtGTrZVHEY"


class FlightSearchToolRequest:
    def __init__(self, user_query: UserQuery):
        self.user_query: UserQuery = user_query
    

    async def run(self) -> List[Quote]:
        """
        Return a list of ``Quote`` objects. All prices are in GBP.
        """
        logger.info(f"Starting flight search: {self.user_query.origin} -> {self.user_query.destination} on {self.user_query.departure_date} for {self.user_query.num_adults} adults")
        
        if self.user_query.departure_date is None:
            departure_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
            logger.info(f"No departure date provided, using default: {departure_date}")

        params = {
            "fly_from":       self.user_query.origin.upper(),
            "fly_to":         self.user_query.destination.upper(),
            "date_from":      self.user_query.departure_date,
            "date_to":        self.user_query.departure_date,
            "adults":         self.user_query.num_adults,
            "children":       0,
            "curr":           CURRENCY,
            "selected_cabins": "M",
            "flight_type":    self.user_query.flight_type.value,
            "limit":          3,
            "sort":           "price",
        }

        logger.debug(f"API request params: {params}")
        headers = {"apikey": API_KEY}

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                logger.info("Making API request to Kiwi...")
                r = await client.get(KIWI_API, params=params, headers=headers)
                r.raise_for_status()
                payload = r.json()
                logger.debug(f"API response: {payload}")

            if "data" not in payload or not payload["data"]:
                logger.warning("No flight data found in API response")
                return []

            quotes: list[Quote] = []
            for flight in payload["data"]:
                segments: list[Segment] = []
                for s in flight["route"]:
                    segments.append(
                        Segment(
                            airline=s["airline"],
                            local_departure=s["local_departure"],
                            local_arrival=s["local_arrival"],
                        )
                    )

                quote = Quote(
                    price=flight["price"],
                    departure=segments[0].local_departure,
                    arrival=segments[-1].local_arrival,
                    carriers=list({seg.airline for seg in segments}),
                    stops=len(segments) - 1,
                    deep_link=flight["deep_link"],
                )
                logger.info(f"Found flight: {quote.model_dump()}")
                quotes.append(quote)

            logger.info(f"Found {len(quotes)} flights")
            return quotes

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during flight search: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during flight search: {str(e)}")
            raise