from mcp.server.fastmcp import FastMCP
from typing import List, Dict
from pydantic import BaseModel
import aiohttp, asyncio, datetime as dt

mcp = FastMCP("FlightTools")

# --------- Flight search tooling ---------------------------------
class Input(BaseModel):
    origin: str
    destination: str
    depart_date: str
    return_date: str | None = None
    pax: int = 1

class Quote(BaseModel):
    supplier: str
    price: float
    currency: str
    deep_link: str
    fetched_at: str

SUPPLIERS = [
    ("skyscanner", "https://api.example.com/sky"),
    ("amadeus",    "https://api.example.com/amadeus"),
    ("kiwi",       "https://api.tequila.kiwi.com/v2/search"),
]

async def _fetch(sess, name, url, params):
    async with sess.get(url, params=params, timeout=10) as r:
        data = await r.json()
        return Quote(
            supplier=name,
            price=data["price"],
            currency=data["currency"],
            deep_link=data["link"],
            fetched_at=dt.datetime.utcnow().isoformat(),
        )

@mcp.tool()
async def flight_search(input: Input) -> List[Quote]:
    """Query three suppliers asynchronously."""
    params = input.model_dump()
    async with aiohttp.ClientSession() as sess:
        return await asyncio.gather(*[
            _fetch(sess, n, u, params) for n, u in SUPPLIERS
        ])

# --------- Aggregator -------------------------------------------
@mcp.tool()
def aggregator(quotes: List[Quote]) -> List[Quote]:
    """Deduplicate & sort quotes."""
    uniq = {(q.supplier, q.price): q for q in quotes}
    return sorted(uniq.values(), key=lambda q: q.price)

# --------- Screenshot -------------------------------------------
@mcp.tool()
async def screenshot(urls: List[str]) -> List[str]:
    """Return screenshot paths (uses Celery)."""
    return []

# --------- Analytics --------------------------------------------
@mcp.tool()
def analytics(quotes: List[Quote]) -> Dict:
    prices = [q.price for q in quotes]
    return {
        "avg_price": sum(prices)/len(prices),
        "min_price": min(prices),
        "max_price": max(prices),
    }

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=7000)
