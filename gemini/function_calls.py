"""
gemini/function_calls.py — bridges Gemini Live `tool_call` events to
core/router.py's ToolDispatcher, and formats the structured result back
into a Gemini FunctionResponse.

This module never executes anything itself — it only translates. All the
actual decision-making (exists? valid? permitted? confirmed?) happens in
the dispatcher, per the security boundary described in both project docs.
"""
from __future__ import annotations

import logging
from typing import Any

from core.router import ToolDispatcher

logger = logging.getLogger("zyro.function_calls")


def handle_function_call(dispatcher: ToolDispatcher, name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run one Gemini function call through the dispatcher and return the
    structured result payload (success/message/data) to embed in the
    FunctionResponse sent back to Gemini."""
    logger.info("Tool call started: %s(%s)", name, {k: v for k, v in args.items() if k != "_confirmation_token"})
    outcome = dispatcher.dispatch(name, args)
    if outcome.executed:
        logger.info("Tool call completed: %s", name)
    else:
        logger.info("Tool call completed without executing: %s -> %s", name, outcome.result.get("message"))
    return outcome.result


async def handle_tool_call(session: Any, dispatcher: ToolDispatcher, tool_call: Any) -> None:
    """
    Consume one Live API `response.tool_call` event: run every requested
    function call through the dispatcher, then send all FunctionResponses
    back in a single batch (mirrors the official SDK example in
    ai.google.dev/gemini-api/docs/live-api/get-started-sdk#handling-tool-calls).
    """
    from google.genai import types  # imported lazily so tests don't need the SDK installed

    function_responses = []
    for fc in tool_call.function_calls:
        result = handle_function_call(dispatcher, fc.name, dict(fc.args or {}))
        function_responses.append(
            types.FunctionResponse(name=fc.name, id=fc.id, response={"result": result})
        )

    await session.send_tool_response(function_responses=function_responses)
