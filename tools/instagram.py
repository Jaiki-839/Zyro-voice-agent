"""
tools/instagram.py -- Instagram Web tools for ZYRO.

Navigation strategy: URL-based only (no pyautogui for search/profile).
  - search_instagram(query) -> https://www.instagram.com/explore/search/keyword/?q=<encoded>
  - open_instagram_profile(username) -> https://www.instagram.com/<username>/
  - open_instagram_reels() -> https://www.instagram.com/<active_target>/reels/
  - All URLs are constructed by this module only; Gemini never provides raw URLs.

Scrolling: delegated to tools/webapp_nav.py (browser_adapter.browser_scroll).

Security:
  - URL-encoding is applied to all user-provided strings before URL construction.
  - webbrowser.open() is the ONLY mechanism used for navigation.
  - No pyautogui for navigation. No DOM access. No JS injection.
  - Gemini calls explicit tools; tools build controlled URLs internally.

Tool result convention: {success: bool, message: str, data: dict | None}
  data always includes "context": session.webapp.to_dict() so Gemini can
  read the updated task context for follow-up commands.
"""
from __future__ import annotations

import logging
import urllib.parse
import webbrowser
from typing import Any

from webapps.browser_adapter import wait_for_browser_ready
from webapps.registry import WEB_APP_REGISTRY

logger = logging.getLogger("zyro.tools.instagram")

_APP = WEB_APP_REGISTRY["instagram"]
_OPEN_TIMEOUT = 8.0  # seconds to wait for browser title


def _result(success: bool, message: str, data: Any = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data}


def _validate_query(query: str) -> tuple[bool, str]:
    """Validate a search query. Returns (ok, error_message)."""
    q = (query or "").strip()
    if not q:
        return False, "A search query is required."
    if len(q) > 200:
        return False, "Search query is too long."
    return True, q


def _validate_username(username: str) -> tuple[bool, str]:
    """
    Validate an Instagram username.
    Allows letters, digits, dots, underscores, hyphens (Instagram rules).
    Returns (ok, cleaned_username_or_error).
    """
    u = (username or "").strip().lstrip("@")
    if not u:
        return False, "A username is required."
    if len(u) > 30:
        return False, f"Username '{u}' is too long (Instagram usernames are max 30 chars)."
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    bad = set(u) - allowed
    if bad:
        return False, f"Username '{u}' contains invalid characters: {sorted(bad)}"
    return True, u


# ---------------------------------------------------------------------------
# Public tool handlers
# ---------------------------------------------------------------------------


def open_instagram(mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """Open the Instagram homepage in the default browser."""
    if mock_mode:
        if session is not None:
            session.webapp.switch_app("instagram")
        return _result(
            True,
            "[mock] Would open Instagram. Instagram is open. What would you like me to do?",
            {"app": "instagram", "ready": True,
             "context": session.webapp.to_dict() if session else {}},
        )

    webbrowser.open(_APP.base_url)
    ready = wait_for_browser_ready("Instagram", timeout=_OPEN_TIMEOUT)

    if session is not None:
        session.webapp.switch_app("instagram")

    if not ready:
        return _result(
            True,
            "Instagram opened, but the readiness check timed out. "
            "It may still be loading -- try your next command in a moment.",
            {"app": "instagram", "ready": False,
             "context": session.webapp.to_dict() if session else {}},
        )

    return _result(
        True,
        "Instagram is open. What would you like me to do?",
        {"app": "instagram", "ready": True,
         "context": session.webapp.to_dict() if session else {}},
    )


def search_instagram(query: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Search Instagram by opening a URL-based search page.

    Constructs: https://www.instagram.com/explore/search/keyword/?q=<encoded_query>
    Gemini never provides the raw URL -- this tool builds it internally.
    """
    ok, val = _validate_query(query)
    if not ok:
        return _result(False, val, None)

    encoded = urllib.parse.quote_plus(val)
    url = f"https://www.instagram.com/explore/search/keyword/?q={encoded}"

    if mock_mode:
        if session is not None:
            session.webapp.update(active_app="instagram", last_action="search", active_target=val)
        return _result(
            True,
            f"[mock] Would search Instagram for '{val}'.",
            {"query": val, "url": url,
             "context": session.webapp.to_dict() if session else {}},
        )

    webbrowser.open(url)
    if session is not None:
        session.webapp.update(active_app="instagram", last_action="search", active_target=val)

    return _result(
        True,
        f"Searching Instagram for '{val}'.",
        {"query": val, "url": url,
         "context": session.webapp.to_dict() if session else {}},
    )


def open_instagram_profile(username: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Open an Instagram profile by constructing: https://www.instagram.com/<username>/

    If username is empty, uses session.webapp.active_target (set by a previous search).
    Gemini never constructs the URL -- this tool does it internally after validation.
    """
    # Resolve username from context if not provided
    resolved = (username or "").strip()
    if not resolved and session is not None:
        resolved = session.webapp.active_target or ""

    ok, val = _validate_username(resolved)
    if not ok:
        return _result(
            False,
            val or "No username provided and no active Instagram target in context.",
            None,
        )

    url = f"https://www.instagram.com/{val}/"

    if mock_mode:
        if session is not None:
            session.webapp.update(
                active_app="instagram", last_action="open_profile",
                active_target=val, active_page="profile",
            )
        return _result(
            True,
            f"[mock] Would open Instagram profile for @{val}.",
            {"username": val, "url": url,
             "context": session.webapp.to_dict() if session else {}},
        )

    webbrowser.open(url)
    if session is not None:
        session.webapp.update(
            active_app="instagram", last_action="open_profile",
            active_target=val, active_page="profile",
        )

    return _result(
        True,
        f"Opening Instagram profile for @{val}.",
        {"username": val, "url": url,
         "context": session.webapp.to_dict() if session else {}},
    )


def open_instagram_reels(username: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Open the Reels section for an Instagram profile.

    Constructs: https://www.instagram.com/<username>/reels/
    If username is empty, uses session.webapp.active_target.
    """
    resolved = (username or "").strip()
    if not resolved and session is not None:
        resolved = session.webapp.active_target or ""

    ok, val = _validate_username(resolved)
    if not ok:
        return _result(False, "No username provided and no active Instagram profile in context.", None)

    url = f"https://www.instagram.com/{val}/reels/"

    if mock_mode:
        if session is not None:
            session.webapp.update(
                active_app="instagram", last_action="open_reels",
                active_target=val, active_page="reels",
            )
        return _result(
            True,
            f"[mock] Would open Reels for @{val}.",
            {"username": val, "url": url,
             "context": session.webapp.to_dict() if session else {}},
        )

    webbrowser.open(url)
    if session is not None:
        session.webapp.update(
            active_app="instagram", last_action="open_reels",
            active_target=val, active_page="reels",
        )

    return _result(
        True,
        f"Opening Reels for @{val}.",
        {"username": val, "url": url,
         "context": session.webapp.to_dict() if session else {}},
    )


def open_instagram_post(username: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Navigate to the posts grid for an Instagram profile.

    Constructs: https://www.instagram.com/<username>/
    (The default Instagram profile view shows posts.)
    """
    resolved = (username or "").strip()
    if not resolved and session is not None:
        resolved = session.webapp.active_target or ""

    ok, val = _validate_username(resolved)
    if not ok:
        return _result(False, "No username provided and no active Instagram profile in context.", None)

    url = f"https://www.instagram.com/{val}/"

    if mock_mode:
        if session is not None:
            session.webapp.update(
                active_app="instagram", last_action="open_post",
                active_target=val, active_page="posts",
            )
        return _result(
            True,
            f"[mock] Would open posts for @{val}.",
            {"username": val, "url": url,
             "context": session.webapp.to_dict() if session else {}},
        )

    webbrowser.open(url)
    if session is not None:
        session.webapp.update(
            active_app="instagram", last_action="open_post",
            active_target=val, active_page="posts",
        )

    return _result(
        True,
        f"Opening posts for @{val}.",
        {"username": val, "url": url,
         "context": session.webapp.to_dict() if session else {}},
    )


def refresh_instagram(mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """Refresh the current Instagram page (F5)."""
    from webapps.browser_adapter import browser_refresh

    if mock_mode:
        return _result(True, "[mock] Would refresh Instagram.", {"context": session.webapp.to_dict() if session else {}})

    ok = browser_refresh()
    if not ok:
        return _result(
            False,
            "Couldn't refresh Instagram. Make sure the browser window is focused. "
            "(pyautogui may not be installed: pip install pyautogui)",
            None,
        )

    if session is not None:
        session.webapp.update(last_action="refresh")

    return _result(True, "Refreshed Instagram.", {"context": session.webapp.to_dict() if session else {}})
