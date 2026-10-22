"""
tools/discord_web.py -- Discord Web tools for ZYRO.

Interaction strategy:
  - Open Discord Web via a fixed controlled URL (discord.com/app).
  - In-app search uses Ctrl+K (Discord quick-search shortcut) via browser_adapter.discord_quick_search().
  - Message sending is a CONFIRM-level action requiring explicit user confirmation.
  - The CONFIRM permission in core/router.py issues a fingerprinted token that Gemini must
    include on the second call to actually execute. The token is tied to (tool, target, message).

Security:
  - No arbitrary keyboard sequences.
  - No DOM access, JS injection, or CDP.
  - discord_quick_search() is the ONLY keyboard automation exposed.
  - discord_type_message() and discord_submit_message() are only called after CONFIRM.
  - Gemini never generates browser automation instructions.

Tool result convention: {success: bool, message: str, data: dict | None}
"""
from __future__ import annotations

import logging
import webbrowser
from typing import Any

from webapps.browser_adapter import (
    discord_quick_search,
    discord_submit_message,
    discord_type_message,
    focus_browser,
    is_available,
    wait_for_browser_ready,
)
from webapps.registry import WEB_APP_REGISTRY

logger = logging.getLogger("zyro.tools.discord")

_APP = WEB_APP_REGISTRY["discord"]
_OPEN_TIMEOUT = 10.0


def _result(success: bool, message: str, data: Any = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data}


def _validate_text(text: str, field_name: str, max_len: int = 500) -> tuple[bool, str]:
    t = (text or "").strip()
    if not t:
        return False, f"{field_name} cannot be empty."
    if len(t) > max_len:
        return False, f"{field_name} is too long (max {max_len} chars)."
    return True, t


# ---------------------------------------------------------------------------
# Public tool handlers
# ---------------------------------------------------------------------------


def open_discord(mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """Open Discord Web in the default browser."""
    if mock_mode:
        if session is not None:
            session.webapp.switch_app("discord")
        return _result(
            True,
            "[mock] Would open Discord. Discord is open. What would you like me to do?",
            {"app": "discord", "ready": True,
             "context": session.webapp.to_dict() if session else {}},
        )

    webbrowser.open(_APP.base_url)
    ready = wait_for_browser_ready("Discord", timeout=_OPEN_TIMEOUT)

    if session is not None:
        session.webapp.switch_app("discord")

    if not ready:
        return _result(
            True,
            "Discord opened, but the readiness check timed out. It may still be loading.",
            {"app": "discord", "ready": False,
             "context": session.webapp.to_dict() if session else {}},
        )

    return _result(
        True,
        "Discord is open. What would you like me to do?",
        {"app": "discord", "ready": True,
         "context": session.webapp.to_dict() if session else {}},
    )


def open_discord_server(server_name: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Navigate to a Discord server using Ctrl+K quick search.

    server_name is typed into Discord's native search panel -- no raw browser automation.
    """
    ok, val = _validate_text(server_name, "Server name", max_len=100)
    if not ok:
        return _result(False, val, None)

    if mock_mode:
        if session is not None:
            session.webapp.update(active_app="discord", active_target=val, last_action="open_server")
        return _result(
            True,
            f"[mock] Would navigate to Discord server '{val}' using Ctrl+K search.",
            {"server": val, "context": session.webapp.to_dict() if session else {}},
        )

    if not is_available():
        return _result(
            False,
            "Discord server navigation requires pyautogui. pip install pyautogui pygetwindow",
            None,
        )

    focused = focus_browser()
    if not focused:
        logger.warning("Could not focus browser for Discord server search")

    sent = discord_quick_search(val)
    if not sent:
        return _result(
            False,
            f"Couldn't open Discord quick search for '{val}'. "
            "Make sure Discord Web is open in the browser.",
            None,
        )

    if session is not None:
        session.webapp.update(active_app="discord", active_target=val, last_action="open_server")

    return _result(
        True,
        f"Navigating to Discord server '{val}'.",
        {"server": val, "context": session.webapp.to_dict() if session else {}},
    )


def open_discord_channel(channel_name: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Navigate to a Discord channel using Ctrl+K quick search.

    channel_name is validated and passed to discord_quick_search().
    """
    ok, val = _validate_text(channel_name, "Channel name", max_len=100)
    if not ok:
        return _result(False, val, None)

    if mock_mode:
        if session is not None:
            session.webapp.update(
                active_app="discord", active_page=f"channel:{val}",
                last_action="open_channel",
            )
        return _result(
            True,
            f"[mock] Would navigate to Discord channel '{val}'.",
            {"channel": val, "context": session.webapp.to_dict() if session else {}},
        )

    if not is_available():
        return _result(
            False,
            "Discord channel navigation requires pyautogui. pip install pyautogui pygetwindow",
            None,
        )

    focused = focus_browser()
    if not focused:
        logger.warning("Could not focus browser for Discord channel search")

    sent = discord_quick_search(val)
    if not sent:
        return _result(
            False,
            f"Couldn't search for Discord channel '{val}'. "
            "Make sure Discord Web is open in the browser.",
            None,
        )

    if session is not None:
        session.webapp.update(
            active_app="discord", active_page=f"channel:{val}",
            last_action="open_channel",
        )

    return _result(
        True,
        f"Navigating to Discord channel '{val}'.",
        {"channel": val, "context": session.webapp.to_dict() if session else {}},
    )


def search_discord(query: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Search Discord using Ctrl+K quick search (servers, channels, users).
    """
    ok, val = _validate_text(query, "Search query", max_len=100)
    if not ok:
        return _result(False, val, None)

    if mock_mode:
        if session is not None:
            session.webapp.update(active_app="discord", last_action="search")
        return _result(
            True,
            f"[mock] Would search Discord for '{val}'.",
            {"query": val, "context": session.webapp.to_dict() if session else {}},
        )

    if not is_available():
        return _result(
            False,
            "Discord search requires pyautogui. pip install pyautogui pygetwindow",
            None,
        )

    focused = focus_browser()
    if not focused:
        logger.warning("Could not focus browser for Discord search")

    sent = discord_quick_search(val)
    if not sent:
        return _result(
            False,
            f"Couldn't open Discord search for '{val}'. "
            "Make sure Discord Web is open.",
            None,
        )

    if session is not None:
        session.webapp.update(active_app="discord", last_action="search")

    return _result(
        True,
        f"Searching Discord for '{val}'.",
        {"query": val, "context": session.webapp.to_dict() if session else {}},
    )


def send_discord_message(message: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Type and submit a message in the currently active Discord channel.

    PERMISSION: CONFIRM -- the ToolDispatcher will require explicit user confirmation
    before this handler is called. The CONFIRM gate ties the token to (tool, message)
    via args_fingerprint, so changing the message invalidates the token.

    Only call this after the user has explicitly confirmed sending.
    """
    ok, val = _validate_text(message, "Message", max_len=2000)
    if not ok:
        return _result(False, val, None)

    # Resolve target from context for the response message
    target_desc = ""
    if session is not None and session.webapp.active_target:
        target_desc = f" to '{session.webapp.active_target}'"
    elif session is not None and session.webapp.active_page:
        target_desc = f" in '{session.webapp.active_page}'"

    if mock_mode:
        if session is not None:
            session.webapp.update(active_app="discord", last_action="send_message")
        return _result(
            True,
            f"[mock] Would send message{target_desc}: '{val}'.",
            {"message": val, "context": session.webapp.to_dict() if session else {}},
        )

    if not is_available():
        return _result(
            False,
            "Sending Discord messages requires pyautogui. pip install pyautogui pygetwindow",
            None,
        )

    focused = focus_browser()
    if not focused:
        logger.warning("Could not confirm browser is focused for Discord message send")

    typed = discord_type_message(val)
    if not typed:
        return _result(
            False,
            f"Couldn't type the message{target_desc}. "
            "Make sure Discord Web is open and a channel is selected.",
            None,
        )

    submitted = discord_submit_message()
    if not submitted:
        return _result(
            False,
            f"Message was typed but couldn't be submitted{target_desc}.",
            None,
        )

    if session is not None:
        session.webapp.update(active_app="discord", last_action="send_message")

    return _result(
        True,
        f"Message sent{target_desc}: '{val}'.",
        {"message": val, "context": session.webapp.to_dict() if session else {}},
    )
