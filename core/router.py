"""
core/router.py — the ZYRO tool dispatcher.

This is the ONLY code path allowed to invoke a tool handler. Every Gemini
function call goes through ToolDispatcher.dispatch(), which enforces the
flow from skills/skill.md #6:

    1. identify function
    2. verify it exists
    3. validate arguments
    4. check permission
    5. ask for confirmation if needed
    6. execute handler
    7. catch errors
    8. return structured result
    (steps 9-10 — sending the response back to Gemini and letting it speak —
     happen in gemini/function_calls.py, which calls this dispatcher.)

Gemini requests actions; this module decides whether they happen.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from core.permissions import ConfirmationManager, PermissionLevel
from core.session import SessionContext
from core.tool_registry import ToolRegistry, ToolValidationError

logger = logging.getLogger("zyro.dispatcher")

# Reserved argument name used by voice/UI layers to redeem a pending
# CONFIRM-level action. Never exposed to Gemini as a real tool parameter —
# it is stripped from the function declaration schema and only consumed here.
CONFIRMATION_TOKEN_ARG = "_confirmation_token"


def _structured_result(success: bool, message: str, data: Any = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data}


def _needs_confirmation_result(tool_name: str, token: str, message: str) -> dict[str, Any]:
    return _structured_result(
        success=False,
        message=message,
        data={"needs_confirmation": True, "tool": tool_name, "confirmation_token": token},
    )


@dataclass
class DispatchOutcome:
    result: dict[str, Any]
    executed: bool  # True only if the underlying handler actually ran


class ToolDispatcher:
    def __init__(
        self,
        registry: ToolRegistry,
        session: SessionContext | None = None,
        confirmations: ConfirmationManager | None = None,
        mock_mode: bool = True,
        state_manager=None,  # core.zyro_state.StateManager | None
    ) -> None:
        self.registry = registry
        self.session = session or SessionContext()
        self.confirmations = confirmations or ConfirmationManager()
        self.mock_mode = mock_mode
        self._state_manager = state_manager

    def dispatch(self, tool_name: str, raw_args: dict[str, Any] | None = None) -> DispatchOutcome:
        raw_args = dict(raw_args or {})
        confirmation_token = raw_args.pop(CONFIRMATION_TOKEN_ARG, None)

        # Sleep gate: block all tools while ZYRO is sleeping, except zyro_sleep
        # itself (which is the transition that wakes/sleeps ZYRO).
        if (
            self._state_manager is not None
            and self._state_manager.is_sleeping()
            and tool_name != "zyro_sleep"
        ):
            logger.info("Tool '%s' blocked: ZYRO is sleeping", tool_name)
            result = _structured_result(
                False,
                "ZYRO is sleeping. Say 'Hey ZYRO, wake up' or type 'wake up' to resume.",
            )
            return DispatchOutcome(result, executed=False)

        # 1 & 2. identify + verify the function exists
        tool = self.registry.get(tool_name)
        if tool is None:
            logger.warning("Dispatch requested unknown tool: %s", tool_name)
            result = _structured_result(False, f"Unknown tool '{tool_name}'.")
            return DispatchOutcome(result, executed=False)

        # 3. validate arguments
        try:
            args = tool.validate_args(raw_args)
        except ToolValidationError as exc:
            logger.warning("Argument validation failed for %s: %s", tool_name, exc)
            result = _structured_result(False, str(exc))
            self.session.record(tool_name, raw_args, result)
            return DispatchOutcome(result, executed=False)

        # 4. check permission (+ 5. confirmation where required)
        if tool.permission == PermissionLevel.RESTRICTED:
            logger.warning("Denied RESTRICTED tool call: %s", tool_name)
            result = _structured_result(
                False,
                f"'{tool_name}' is a restricted operation and cannot be performed this way.",
            )
            self.session.record(tool_name, args, result)
            return DispatchOutcome(result, executed=False)

        if tool.permission == PermissionLevel.CONFIRM:
            if confirmation_token is None:
                ticket = self.confirmations.request(tool_name, args)
                logger.info("Confirmation required for %s (token issued)", tool_name)
                result = _needs_confirmation_result(
                    tool_name,
                    ticket.token,
                    f"'{tool_name}' requires confirmation before it runs. "
                    f"Please confirm explicitly before this is executed.",
                )
                self.session.record(tool_name, args, result)
                return DispatchOutcome(result, executed=False)

            if not self.confirmations.confirm(confirmation_token, tool_name, args):
                logger.warning("Invalid or stale confirmation for %s", tool_name)
                result = _structured_result(
                    False,
                    "That confirmation is invalid, expired, or does not match this action. "
                    "Please try again and confirm explicitly.",
                )
                self.session.record(tool_name, args, result)
                return DispatchOutcome(result, executed=False)

        # 6 & 7. execute handler, catching everything
        try:
            payload = tool.handler(mock_mode=self.mock_mode, session=self.session, **args)
            if not isinstance(payload, dict) or "success" not in payload:
                raise TypeError(f"Handler for '{tool_name}' returned a non-structured result")
            result = payload
        except Exception as exc:  # noqa: BLE001 — this boundary must never leak a raw traceback upward
            logger.exception("Handler for %s raised an exception", tool_name)
            result = _structured_result(False, f"'{tool_name}' failed: {exc}")
            self.session.record(tool_name, args, result)
            return DispatchOutcome(result, executed=False)

        # 8. structured result, recorded for context resolution
        self.session.record(tool_name, args, result)
        return DispatchOutcome(result, executed=True)
