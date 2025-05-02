# agent/state.py
from pydantic import BaseModel, Field
from typing import List, Dict

class GraphState(BaseModel):
    """
    Canonical state object shared by all LangGraph nodes.
    Every field is optional at start; tools fill them in.
    """
    user_query: str
    quotes:        List[Dict] = Field(default_factory=list)
    agg_quotes:    List[Dict] = Field(default_factory=list)
    screenshots:   List[str]  = Field(default_factory=list)
    analytics:     Dict       = Field(default_factory=dict)
    final_markdown:str        = ""
