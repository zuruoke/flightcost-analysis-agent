import asyncio
from pydantic import BaseModel
from typing import List
import aiohttp, datetime as dt

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
    ("kiwi",       "https://api.tequila.kiwi.com/v2/search")
]

async def _fetch(session, supplier, url, params):
    async with session.get(url, params=params, timeout=30) as r:
        data = await r.json()
        return Quote(
            supplier=supplier,
            price=data["price"],
            currency=data["currency"],
            deep_link=data["link"],
            fetched_at=dt.datetime.utcnow().isoformat()
        )

async def run(input: Input) -> List[Quote]:
    params = input.model_dump()
    async with aiohttp.ClientSession() as sess:
        quotes = await asyncio.gather(*[
            _fetch(sess, sup, url, params) for sup, url in SUPPLIERS
        ])
    return quotes
