# ──────────────────────────── helper dataclasses ────────────────────────────
from typing import List
from pydantic import BaseModel


class Segment(BaseModel):
    airline: str
    local_departure: str
    local_arrival:   str


class Quote(BaseModel):
    price: int
    departure: str
    arrival:   str
    carriers:  List[str]
    stops:     int
    deep_link: str
