from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class FlightClass(str, Enum):
    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"

class FlightType(str, Enum):
    ONE_WAY = "oneway"
    ROUND_TRIP = "roundtrip"

class Duration(BaseModel):
    startDateTime: datetime
    endDateTime: datetime

class UserQuery(BaseModel):
    origin: str
    destination: str
    num_adults: Optional[int] = 1
    num_children: Optional[int] = 0
    flight_class: Optional[FlightClass] = FlightClass.ECONOMY
    departure_date: Optional[str] = None
    duration: Optional[Duration] = None
    flight_type: Optional[FlightType] = FlightType.ONE_WAY

class GraphState(BaseModel):
    user_query: UserQuery
    quotes: Optional[List[dict]] = None
    agg_quotes: Optional[dict] = None
    screenshots: Optional[List[str]] = None
    analytics: Optional[dict] = None
