from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class GraphState(BaseModel):
    # input fields
    origin: str
    destination: str
    num_adults: int = 1
    departure_date: Optional[str] = None
    # outputs at each stage
    quotes: Optional[List[dict]] = None
    agg_quotes: Optional[dict] = None
    screenshots: Optional[List[str]] = None
    analytics: Optional[dict] = None
