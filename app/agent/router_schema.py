from typing import Literal, Dict
from pydantic import BaseModel
from app.agent.constants import ALLOWED_TOOL_NAMES

class RouterDecision(BaseModel):
    """The exact JSON layout the router LLM **must** produce."""
    tool_name: Literal[*ALLOWED_TOOL_NAMES]
    tool_args: Dict = {}
