"""
core/permissions.py — the permission layer.

Every tool in the registry declares a PermissionLevel. This module is the
single source of truth for what happens at each level, and it is the last
thing standing between "Gemini asked for X" and "X actually happened".

    SAFE        — dispatcher may execute immediately.
    CONFIRM     — dispatcher must hold a matching, unexpired confirmation
                  for *this specific pending call* before executing.
    RESTRICTED  — never auto-executed by voice in V0.1. Always denied by
                  the dispatcher. Reserved for future explicit, out-of-band
                  approval (e.g. a UI dialog), never a spoken "yes".

Local permission decisions always win over whatever Gemini requests —
Gemini decides what it wants to do, ZYRO decides whether it is allowed.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from enum import Enum


class PermissionLevel(str, Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    RESTRICTED = "RESTRICTED"


@dataclass
class PendingConfirmation:
    """A single, one-shot confirmation ticket tied to one specific tool call."""

    token: str
    tool_name: str
    args_fingerprint: str
    created_at: float
    ttl_seconds: float = 60.0

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds


def _fingerprint(tool_name: str, args: dict) -> str:
    """Cheap, order-independent fingerprint of a call so a confirmation can't be
    replayed against a different call just because the tool name matches."""
    items = sorted((str(k), str(v)) for k, v in (args or {}).items())
    return f"{tool_name}:{items}"


class ConfirmationManager:
    """
    Tracks pending CONFIRM-level actions.

    Confirmation must be explicit and tied to the current pending action —
    silence is not approval, and a stale confirmation can never be reused
    for a new call (see skills/skill.md #15).
    """

    def __init__(self) -> None:
        self._pending: dict[str, PendingConfirmation] = {}

    def request(self, tool_name: str, args: dict) -> PendingConfirmation:
        """Create a fresh confirmation ticket for a CONFIRM-level call."""
        ticket = PendingConfirmation(
            token=uuid.uuid4().hex,
            tool_name=tool_name,
            args_fingerprint=_fingerprint(tool_name, args),
            created_at=time.time(),
        )
        self._pending[ticket.token] = ticket
        return ticket

    def confirm(self, token: str, tool_name: str, args: dict) -> bool:
        """
        Redeem a confirmation token. Returns True only if the token exists,
        has not expired, and matches the exact tool + arguments it was issued
        for. The ticket is consumed either way (one-shot).
        """
        ticket = self._pending.pop(token, None)
        if ticket is None:
            return False
        if ticket.is_expired():
            return False
        if ticket.tool_name != tool_name:
            return False
        if ticket.args_fingerprint != _fingerprint(tool_name, args):
            return False
        return True

    def discard_expired(self) -> None:
        expired = [t for t, c in self._pending.items() if c.is_expired()]
        for t in expired:
            self._pending.pop(t, None)
