"""
Tracing utilities for the flight search agent.

This module provides decorators and utilities for logging the input and output
of agent nodes in the flight search workflow. It helps with debugging and
monitoring the agent's execution flow.
"""

import functools
import inspect
import json
import logging
from datetime import datetime, timezone
from typing import Any

# Configure logging
log = logging.getLogger("trace")
logging.basicConfig(level=logging.INFO)

def trace(name: str):
    """
    Decorator for logging input and output of agent nodes.
    
    This decorator logs:
    - The input state when a node starts execution
    - The output delta when a node completes execution
    
    Args:
        name (str): The name of the node being traced
        
    Returns:
        Callable: A decorated function that logs its execution
    """
    def _decorator(fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def _aw(state, *a, **kw):
                _log_in(name, state)
                delta = await fn(state, *a, **kw)
                _log_out(name, delta)
                return delta
            return _aw
        else:
            @functools.wraps(fn)
            def _w(state, *a, **kw):
                _log_in(name, state)
                delta = fn(state, *a, **kw)
                _log_out(name, delta)
                return delta
            return _w
    return _decorator

def _log_in(name: str, state: Any) -> None:
    """
    Log the input state of a node.
    
    Args:
        name (str): Name of the node
        state (Any): Input state object
    """
    log.info(
        "[%s] ▶︎ %s  input=%s",
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        name,
        {k: getattr(state, k) for k in state.model_fields_set},
    )

def _log_out(name: str, delta: Any) -> None:
    """
    Log the output delta of a node.
    
    Args:
        name (str): Name of the node
        delta (Any): Output delta object
    """
    log.info(
        "[%s] ◀︎ %s  delta=%s",
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        name,
        delta,
    )

def _as_python(obj: Any) -> Any:
    """
    Convert JSON-encoded strings into Python objects recursively.
    
    This is particularly useful for handling responses from MCP/STDIO tool calls
    that may return JSON-encoded strings.
    
    Args:
        obj (Any): Input object that may contain JSON-encoded strings
        
    Returns:
        Any: Object with all JSON-encoded strings converted to Python objects
    """
    if isinstance(obj, str):
        try:
            return _as_python(json.loads(obj))
        except json.JSONDecodeError:
            return obj
    if isinstance(obj, list):
        return [_as_python(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _as_python(v) for k, v in obj.items()}
    return obj 