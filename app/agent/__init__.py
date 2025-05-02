# agent/__init__.py
"""
Lazy-load the compiled graph so `from app.agent import flight_agent`
just works.
"""
from agent.graph import flight_agent   # noqa: F401
