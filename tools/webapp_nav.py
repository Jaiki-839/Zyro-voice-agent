"""
tools/webapp_nav.py -- Shared navigation tools usable across all web apps.

These tools wrap the controlled browser_adapter actions (scroll, back,
forward, refresh) and attach them to the active WebAppContext.

Tools:
  scroll_webapp(app, direction, amount)  -- constrained scroll (up/down, small/medium/large)
  go_back_webapp(app)                    -- Alt+Left
  go_forward_webapp(app)                 -- Alt+Right
  refresh_webapp(app)                    -- F5

The `app` parameter is optional. If provided, it's validated against supported apps.
If omitted, the currently active app from session.webapp is used.
"""
from __future__ import annotations

import logging
from typing import Any

from core.webapp_context import SUPPORTED_APPS
from webapps.browser_adapter import (
    ALLOWED_SCROLL_AMOUNTS,
    ALLOWED_SCROLL_DIRECTIONS,
    browser_back,
    browser_forward,
    browser_refresh,
    browser_scroll,
    is_available,
)

logger = logging.getLogger("zyro.tools.webapp_nav")


def _result(success: bool, message: str, data: Any = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data}


def _resolve_app(app: str, session) -> str | None:
    """Resolve the target app: from arg, then from session context."""
    if app:
        return app.lower().strip()
    if session is not None:
        return session.webapp.active_app
    return None


def _require_browser_automation(fn_name: str) -> dict | None:
    """Return an error result if pyautogui is not available."""
    if not is_available():
        return _result(
            False,
            f"'{fn_name}' requires pyautogui for keyboard control. "
            "Install it with: pip install pyautogui pygetwindow",
            None,
        )
    return None


# ---------------------------------------------------------------------------
# Public tool handlers
# ---------------------------------------------------------------------------


def scroll_webapp(
    app: str = "",
    direction: str = "down",
    amount: str = "medium",
    mock_mode: bool = False,
    session=None,
    **_,
) -> dict[str, Any]:
    """
    Scroll the currently active web app page.

    direction: "up" or "down"
    amount: "small", "medium", or "large"
    app: optional override for active app (defaults to session.webapp.active_app)

    Uses browser_adapter.browser_scroll() -- constrained values only.
    No arbitrary scroll amounts or coordinates are accepted.
    """
    direction = (direction or "down").lower().strip()
    amount = (amount or "medium").lower().strip()

    if direction not in ALLOWED_SCROLL_DIRECTIONS:
        return _result(False, f"Invalid scroll direction '{direction}'. Use 'up' or 'down'.", None)

    if amount not in ALLOWED_SCROLL_AMOUNTS:
        return _result(
            False,
            f"Invalid scroll amount '{amount}'. Use 'small', 'medium', or 'large'.",
            None,
        )

    resolved_app = _resolve_app(app, session)

    if mock_mode:
        if session is not None:
            session.webapp.update(last_action=f"scroll_{direction}")
        return _result(
            True,
            f"[mock] Would scroll {direction} ({amount}) on {resolved_app or 'current page'}.",
            {"direction": direction, "amount": amount, "app": resolved_app,
             "context": session.webapp.to_dict() if session else {}},
        )

    err = _require_browser_automation("scroll_webapp")
    if err:
        return err

    ok = browser_scroll(direction, amount)
    if not ok:
        return _result(
            False,
            f"Couldn't scroll {direction}. Make sure the browser window is in focus.",
            None,
        )

    if session is not None:
        session.webapp.update(last_action=f"scroll_{direction}")

    return _result(
        True,
        f"Scrolled {direction} ({amount}).",
        {"direction": direction, "amount": amount, "app": resolved_app,
         "context": session.webapp.to_dict() if session else {}},
    )


def go_back_webapp(app: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """Go back in the browser (Alt+Left) on the current web app."""
    resolved_app = _resolve_app(app, session)

    if mock_mode:
        if session is not None:
            session.webapp.update(last_action="go_back")
        return _result(
            True,
            f"[mock] Would go back on {resolved_app or 'current page'}.",
            {"app": resolved_app, "context": session.webapp.to_dict() if session else {}},
        )

    err = _require_browser_automation("go_back_webapp")
    if err:
        return err

    ok = browser_back()
    if not ok:
        return _result(False, "Couldn't go back. Make sure the browser window is focused.", None)

    if session is not None:
        session.webapp.update(last_action="go_back")

    return _result(
        True, "Went back.",
        {"app": resolved_app, "context": session.webapp.to_dict() if session else {}},
    )


def go_forward_webapp(app: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """Go forward in the browser (Alt+Right) on the current web app."""
    resolved_app = _resolve_app(app, session)

    if mock_mode:
        if session is not None:
            session.webapp.update(last_action="go_forward")
        return _result(
            True,
            f"[mock] Would go forward on {resolved_app or 'current page'}.",
            {"app": resolved_app, "context": session.webapp.to_dict() if session else {}},
        )

    err = _require_browser_automation("go_forward_webapp")
    if err:
        return err

    ok = browser_forward()
    if not ok:
        return _result(False, "Couldn't go forward. Make sure the browser window is focused.", None)

    if session is not None:
        session.webapp.update(last_action="go_forward")

    return _result(
        True, "Went forward.",
        {"app": resolved_app, "context": session.webapp.to_dict() if session else {}},
    )


def refresh_webapp(app: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """Refresh the current web app page (F5)."""
    resolved_app = _resolve_app(app, session)

    if mock_mode:
        if session is not None:
            session.webapp.update(last_action="refresh")
        return _result(
            True,
            f"[mock] Would refresh {resolved_app or 'current page'}.",
            {"app": resolved_app, "context": session.webapp.to_dict() if session else {}},
        )

    err = _require_browser_automation("refresh_webapp")
    if err:
        return err

    ok = browser_refresh()
    if not ok:
        return _result(False, "Couldn't refresh. Make sure the browser window is focused.", None)

    if session is not None:
        session.webapp.update(last_action="refresh")

    return _result(
        True, f"Refreshed {resolved_app or 'page'}.",
        {"app": resolved_app, "context": session.webapp.to_dict() if session else {}},
    )
