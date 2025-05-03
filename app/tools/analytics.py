from __future__ import annotations
from statistics import median
from typing import List
from app.tools.models.analytics_model import Analytics, Bucket
from app.tools.models.flight_search_model import Quote

_BUCKET_SIZE = 50 

def analyse_quotes_request(quotes: List[Quote]) -> Analytics:
    if not quotes:
        raise ValueError("No quotes supplied for analysis")

    prices = [q.price for q in quotes]
    min_p, max_p = min(prices), max(prices)

    # crude histogram so the LLM can pick “price bands”
    bucket_map: dict[tuple[int, int], list[Quote]] = {}
    for q in quotes:
        lo = (q.price // _BUCKET_SIZE) * _BUCKET_SIZE
        hi = lo + _BUCKET_SIZE - 1
        bucket_map.setdefault((lo, hi), []).append(q)

    buckets: list[Bucket] = [
        Bucket(range=(lo, hi), count=len(v), sample=v[0].deep_link)
        for (lo, hi), v in sorted(bucket_map.items())
    ]

    return Analytics(
        min_price=min_p,
        max_price=max_p,
        median_price=median(prices),
        buckets=buckets,
    )
