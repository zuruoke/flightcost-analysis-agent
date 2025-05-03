from statistics import mean
from typing import Dict, List
from app.tools.models.aggregator_model import CarrierStats
from app.tools.models.aggregator_model import Aggregation
from app.tools.models.flight_search_model import Quote


def aggregate_quotes_request(quotes: List[Quote]) -> Aggregation:
    """
    Crunch basic stats so the LLM can present a concise table / paragraph.
    """
    if not quotes:
        raise ValueError("No quotes supplied")

    prices   = [q.price for q in quotes]
    carriers = set(c for q in quotes for c in q.carriers)

    # per-carrier min / max / count
    stats: Dict[str, CarrierStats] = {}
    for q in quotes:
        for c in q.carriers:
            s = stats.setdefault(c, CarrierStats(count=0, min=q.price, max=q.price))
            s.count += 1
            s.min = min(s.min, q.price)
            s.max = max(s.max, q.price)

    return Aggregation(
        cheapest=min(prices),
        average=round(mean(prices), 2),
        most_expensive=max(prices),
        carriers=sorted(carriers),
        by_carrier=stats,
    )