from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List
import os
import httpx
from app.tools.models.flight_search_model import Quote, Segment

KIWI_API   = "https://api.tequila.kiwi.com/v2/search"
CURRENCY   = "GBP"
API_KEY    = "FENuirN6cHfnRL2Vu2cxVWEtGTrZVHEY"

async def flight_search_request(
    origin: str,
    destination: str,
    number_of_adults: int = 1,
    departure_date: Optional[str] = None,
) -> List[Quote]:
    """
    Return a list of ``Quote`` objects. All prices are in GBP.
    """
    if departure_date is None:
        departure_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")

    params = {
        "fly_from":       origin.upper(),
        "fly_to":         destination.upper(),
        "date_from":      departure_date,
        "date_to":        departure_date,
        "adults":         number_of_adults,
        "children":       0,
        "curr":           CURRENCY,
        "selected_cabins": "M",
        "flight_type":    "oneway",
        "limit":          3,
        "sort":           "price",
    }

    headers = {"apikey": API_KEY}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(KIWI_API, params=params, headers=headers)
        r.raise_for_status()
        payload = r.json()

    if "data" not in payload or not payload["data"]:
        return []                                                # <- empty list is fine

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

        quotes.append(
            Quote(
                price=flight["price"],
                departure=segments[0].local_departure,
                arrival=segments[-1].local_arrival,
                carriers=list({seg.airline for seg in segments}),
                stops=len(segments) - 1,
                deep_link=flight["deep_link"],
            )
        )

    return quotes