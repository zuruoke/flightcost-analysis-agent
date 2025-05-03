# from pathlib import Path
# import importlib, inspect, yaml
# from typing import Any, Dict
# from langchain.tools import StructuredTool
# from pydantic import create_model

# def _build_args_schema(input_schema: Dict[str, Any]):
#     """Turn the JSON-Schema 'input' block into a Pydantic model."""
#     fields = {}
#     for name, spec in input_schema["properties"].items():
#         typ = {"string": str, "number": float, "integer": int}.get(spec["type"], Any)
#         default = ... if name in input_schema.get("required", []) else None
#         fields[name] = (typ, default)
#     return create_model("ArgsSchema", **fields)  # type: ignore

# def load_tool_from_manifest(path: Path) -> StructuredTool:
#     data = yaml.safe_load(path.read_text())
  
#     handler_uri: str = data["runtime"]["handler"]
#     if not handler_uri.startswith("local://"):
#         raise ValueError("This loader only supports local:// handlers")
#     mod_path, func_name = handler_uri[len("local://"):].split(":")
#     func = getattr(importlib.import_module(mod_path), func_name)

   
#     args_schema = _build_args_schema(data["input"])

    
#     return StructuredTool.from_function(
#         func=func,
#         name=data["name"],
#         description=data.get("description", ""),
#         args_schema=args_schema,
#     )
