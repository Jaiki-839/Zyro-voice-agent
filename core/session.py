"""
core/session.py — short-term conversation context.

Keeps enough recent state that references like "that file", "the second
one", or "the latest one" can be resolved against recent tool results
(master prompt section 16 / skills/skill.md #21). This is intentionally
*not* the persistent memory described in the V0.4 roadmap — see
memory/memory.py for that; this class only lives for one running session.

Also carries `webapp`: a temporary WebAppContext tracking the active web
app task (Instagram, Discord, WhatsApp, YouTube, Spotify). Never persisted.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from core.webapp_context import WebAppContext


@dataclass
class ToolCallRecord:
    tool_name: str
    args: dict[str, Any]
    result: dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class SessionContext:
    def __init__(self, max_history: int = 50) -> None:
        self.max_history = max_history
        self.history: list[ToolCallRecord] = []
        # The most recent structured "list of things" a tool returned
        # (e.g. search_files results, list_applications results), so
        # "open the second one" / "the latest one" can resolve.
        self.last_result_list: list[dict[str, Any]] = []
        self.last_result_list_tool: str | None = None
        # Temporary web app task context (never persisted).
        # Updated by webapp tools on success; cleared on app switch.
        self.webapp = WebAppContext()

    def record(self, tool_name: str, args: dict[str, Any], result: dict[str, Any]) -> None:
        self.history.append(ToolCallRecord(tool_name, dict(args), result))
        if len(self.history) > self.max_history:
            self.history.pop(0)

        data = result.get("data")
        if result.get("success") and isinstance(data, dict) and isinstance(data.get("results"), list):
            self.last_result_list = data["results"]
            self.last_result_list_tool = tool_name

    def resolve_ordinal_reference(self, phrase: str) -> dict[str, Any] | None:
        """Resolve simple references like 'the first one', 'the second one',
        'the latest one', 'that file' against the last list-shaped result.
        This is a small, explicit helper — Gemini is expected to do most of
        this resolution itself using the conversation context; this exists
        as a local fallback tools can call into."""
        if not self.last_result_list:
            return None

        phrase = phrase.lower().strip()
        ordinals = {
            "first": 0, "1st": 0,
            "second": 1, "2nd": 1,
            "third": 2, "3rd": 2,
            "fourth": 3, "4th": 3,
            "fifth": 4, "5th": 4,
        }
        for word, index in ordinals.items():
            if word in phrase and index < len(self.last_result_list):
                return self.last_result_list[index]

        if "last" in phrase or "latest" in phrase:
            return self.last_result_list[-1]
        if "that" in phrase and len(self.last_result_list) == 1:
            return self.last_result_list[0]
        return None

    def recent_summary(self, n: int = 5) -> list[dict[str, Any]]:
        """Compact summary of the last n tool calls, useful for logging/UI."""
        return [
            {
                "tool": r.tool_name,
                "args": r.args,
                "success": r.result.get("success"),
                "message": r.result.get("message"),
            }
            for r in self.history[-n:]
        ]
