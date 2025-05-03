# ───────────────────────── shared Quote schema ──────────────────────────────
from typing import Dict, List
from pydantic import BaseModel, Field


# ──────────────────────────── Aggregation result ────────────────────────────
class CarrierStats(BaseModel):
    count: int
    min:   int
    max:   int


class Aggregation(BaseModel):
    cheapest:       int
    average:        float
    most_expensive: int = Field(..., alias="most_expensive")
    carriers:       List[str]
    by_carrier:     Dict[str, CarrierStats]