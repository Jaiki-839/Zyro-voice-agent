"""
core/webapp_context.py -- Temporary web app task context for the current session.

This is NOT persistent memory. It is cleared/updated as the user moves between
web apps. It mirrors what Gemini tracks in its own conversation context, giving
tool handlers an accessible Python-side view of the current task.

Nothing here is persisted to disk. On restart it resets to empty.
Never stores passwords, cookies, tokens, or any credentials.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Names of supported web applications (canonical lowercase keys).
SUPPORTED_APPS: frozenset[str] = frozenset(
    {"instagram", "discord", "whatsapp", "youtube", "spotify"}
)


@dataclass
class WebAppContext:
    """
    Temporary task state for the current web app interaction.

    Updated by tool handlers on success.
    Read back by Gemini via the `context` field in tool results.

    Fields:
        active_app      -- canonical app name ("instagram", "discord", etc.) or None
        active_target   -- current user / contact / server / channel name or None
        active_page     -- current page/section ("profile", "reels", "channel", etc.) or None
        active_section  -- sub-section within the current page or None
        last_action     -- name of the last successful tool that ran or None
    """

    active_app: str | None = None
    active_target: str | None = None
    active_page: str | None = None
    active_section: str | None = None
    last_action: str | None = None

    def update(self, **kwargs: Any) -> None:
        """Merge keyword arguments into this context.  Only known fields are accepted."""
        allowed = {"active_app", "active_target", "active_page", "active_section", "last_action"}
        for key, value in kwargs.items():
            if key in allowed:
                setattr(self, key, value)

    def switch_app(self, app: str) -> None:
        """Switch to a new app, clearing target/page/section."""
        self.active_app = app
        self.active_target = None
        self.active_page = None
        self.active_section = None
        self.last_action = f"open_{app}"

    def clear(self) -> None:
        """Reset all context."""
        self.active_app = None
        self.active_target = None
        self.active_page = None
        self.active_section = None
        self.last_action = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict for inclusion in tool result `data.context`."""
        return {
            "active_app": self.active_app,
            "active_target": self.active_target,
            "active_page": self.active_page,
            "active_section": self.active_section,
            "last_action": self.last_action,
        }

    def is_active(self, app: str) -> bool:
        """Return True if the given app is currently active."""
        return self.active_app == app

    def __repr__(self) -> str:
        return (
            f"WebAppContext(app={self.active_app!r}, target={self.active_target!r}, "
            f"page={self.active_page!r}, section={self.active_section!r})"
        )
