from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List

class Quote(BaseModel):
    price: int
    departure: str
    arrival:   str
    carriers:  List[str]
    stops:     int
    deep_link: str


class Bucket(BaseModel):
    range:  tuple[int, int] = Field(..., description="GBP price bracket")
    count:  int
    sample: str             = Field(..., description="deep_link of 1 quote")


class Analytics(BaseModel):
    min_price:      int
    max_price:      int
    median_price:   float
    buckets:        List[Bucket]  # simple histogram for visual LLMs
