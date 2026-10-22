"""
core/tool_registry.py — the single source of truth for what tools ZYRO has.

A Tool bundles everything skills/skill.md #7 and the master prompt's
"Tool Contract" (section 8) require: name, description, typed parameters,
a permission level, and the handler that implements it. The dispatcher
(core/router.py) is the only thing that ever calls a handler directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from core.permissions import PermissionLevel

# A handler takes validated kwargs and returns a plain dict payload.
# It must never raise for "expected" failures (file not found, app not found,
# etc.) — it should return {"success": False, "message": ..., "data": None}
# in those cases. Unexpected exceptions are still caught by the dispatcher,
# but handlers shouldn't rely on that for anything normal.
ToolHandler = Callable[..., dict[str, Any]]


class ToolValidationError(ValueError):
    """Raised when arguments don't match a tool's declared parameter schema."""


@dataclass(frozen=True)
class ToolParameter:
    name: str
    type: str  # "string" | "integer" | "number" | "boolean"
    description: str = ""
    required: bool = True
    enum: tuple[str, ...] | None = None
    default: Any = None

    def to_json_schema(self) -> dict[str, Any]:
        schema: dict[str, Any] = {"type": self.type, "description": self.description}
        if self.enum:
            schema["enum"] = list(self.enum)
        return schema


_PY_TYPE_BY_JSON_TYPE = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
}


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    permission: PermissionLevel
    handler: ToolHandler
    parameters: tuple[ToolParameter, ...] = field(default_factory=tuple)

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate + coerce incoming args against this tool's schema.
        Raises ToolValidationError on anything that doesn't fit."""
        args = dict(args or {})
        validated: dict[str, Any] = {}
        known = {p.name for p in self.parameters}

        unexpected = set(args) - known
        if unexpected:
            raise ToolValidationError(
                f"{self.name}: unexpected argument(s) {sorted(unexpected)}"
            )

        for param in self.parameters:
            if param.name not in args:
                if param.required and param.default is None:
                    raise ToolValidationError(f"{self.name}: missing required argument '{param.name}'")
                validated[param.name] = param.default
                continue

            value = args[param.name]
            expected = _PY_TYPE_BY_JSON_TYPE.get(param.type)
            if expected and not isinstance(value, expected):
                # allow int->float and numeric strings for booleans-in-disguise, but
                # otherwise be strict — this is a security boundary, not a UI form.
                if param.type == "number" and isinstance(value, bool):
                    raise ToolValidationError(f"{self.name}: '{param.name}' must be a number")
                if not (param.type == "number" and isinstance(value, (int, float))):
                    raise ToolValidationError(
                        f"{self.name}: '{param.name}' must be of type {param.type}, got {type(value).__name__}"
                    )
            if param.enum and value not in param.enum:
                raise ToolValidationError(
                    f"{self.name}: '{param.name}' must be one of {param.enum}, got {value!r}"
                )
            validated[param.name] = value

        return validated

    def to_gemini_function_declaration(self) -> dict[str, Any]:
        """Gemini function-declaration JSON schema for this tool."""
        properties = {p.name: p.to_json_schema() for p in self.parameters}
        required = [p.name for p in self.parameters if p.required and p.default is None]
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


class ToolRegistry:
    """Central registry. Nothing else in ZYRO should hold its own tool dict."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def exists(self, name: str) -> bool:
        return name in self._tools

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def to_gemini_function_declarations(self) -> list[dict[str, Any]]:
        return [t.to_gemini_function_declaration() for t in self._tools.values()]
