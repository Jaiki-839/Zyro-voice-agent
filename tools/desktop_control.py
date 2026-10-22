"""
tools/desktop_control.py -- Window focus, minimize, maximize, restore, close.

All operations use the Windows ctypes API (user32.dll).  No pywin32 required.
No taskkill, no process termination, no shell execution.

close_window sends WM_CLOSE to the target window -- the application may
refuse this (e.g. an unsaved document dialog).  This is identical to the
user pressing Alt+F4 on a window and is classified SAFE.

focus_application finds an existing window by title substring.  It does NOT
launch the application.  For launching, use open_application.

switch_app sends a single Alt+Tab to cycle to the previous window.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import sys
from typing import Any

logger = logging.getLogger("zyro.desktop")

# -- ctypes setup -----------------------------------------------------------

if sys.platform == "win32":
    _user32 = ctypes.windll.user32  # type: ignore[attr-defined]
else:
    _user32 = None  # type: ignore[assignment]

# ShowWindow commands
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9
SW_SHOW = 5

# PostMessage / SendMessage constants
WM_CLOSE = 0x0010
WM_SYSCOMMAND = 0x0112
SC_CLOSE = 0xF060

# keybd_event flags
KEYEVENTF_KEYUP = 0x0002

# Virtual keys for Alt+Tab
VK_MENU = 0x12   # Alt
VK_TAB = 0x09


def _require_windows(tool_name: str) -> dict[str, Any] | None:
    if sys.platform != "win32" or _user32 is None:
        return {
            "success": False,
            "message": f"'{tool_name}' is only available on Windows.",
            "data": None,
        }
    return None


# ---------------------------------------------------------------------------
# Window enumeration
# ---------------------------------------------------------------------------

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)


def _find_window_by_title(query: str) -> int | None:
    """Find the first visible foreground window whose title contains *query*
    (case-insensitive).  Returns the HWND or None."""
    query_lower = query.strip().lower()
    matches: list[int] = []

    def _cb(hwnd: int, _lparam: int) -> bool:
        if not _user32.IsWindowVisible(hwnd):
            return True
        length = _user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        _user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.lower()
        if query_lower in title:
            matches.append(hwnd)
        return True

    _user32.EnumWindows(EnumWindowsProc(_cb), 0)
    return matches[0] if matches else None


def _active_window() -> int:
    """Return HWND of the currently active foreground window."""
    return _user32.GetForegroundWindow()


def _send_key(vk: int) -> None:
    """Press and release a virtual key."""
    _user32.keybd_event(vk, 0, 0, 0)
    _user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def close_window(
    app_name: str = "",
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Send WM_CLOSE to the named window (or the active window if no name)."""
    err = _require_windows("close_window")
    if err:
        return err

    if mock_mode:
        target = f"'{app_name}'" if app_name else "the active window"
        return {"success": True, "message": f"[mock] Would close {target}.", "data": None}

    if app_name:
        hwnd = _find_window_by_title(app_name)
        if hwnd is None:
            return {
                "success": False,
                "message": f"Could not find an open window matching '{app_name}'.",
                "data": None,
            }
    else:
        hwnd = _active_window()
        if not hwnd:
            return {"success": False, "message": "No active window found.", "data": None}

    _user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    name_str = app_name or "Active window"
    logger.info("WM_CLOSE sent to hwnd %s (%s)", hwnd, name_str)
    return {"success": True, "message": f"{name_str} close request sent.", "data": {"hwnd": hwnd}}


def switch_app(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Send Alt+Tab to switch to the previous window."""
    err = _require_windows("switch_app")
    if err:
        return err

    if mock_mode:
        return {"success": True, "message": "[mock] Would send Alt+Tab.", "data": None}

    _user32.keybd_event(VK_MENU, 0, 0, 0)
    _user32.keybd_event(VK_TAB, 0, 0, 0)
    _user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
    _user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    logger.info("Alt+Tab sent (switch_app)")
    return {"success": True, "message": "Switched to the previous application.", "data": None}


def minimize_window(
    app_name: str = "",
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Minimize the named window (or the active window)."""
    err = _require_windows("minimize_window")
    if err:
        return err

    if mock_mode:
        target = f"'{app_name}'" if app_name else "the active window"
        return {"success": True, "message": f"[mock] Would minimize {target}.", "data": None}

    hwnd = _find_window_by_title(app_name) if app_name else _active_window()
    if not hwnd:
        return {"success": False, "message": "No matching window found.", "data": None}

    _user32.ShowWindow(hwnd, SW_MINIMIZE)
    return {"success": True, "message": f"{'Window' if not app_name else app_name} minimized.", "data": None}


def maximize_window(
    app_name: str = "",
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Maximize the named window (or the active window)."""
    err = _require_windows("maximize_window")
    if err:
        return err

    if mock_mode:
        target = f"'{app_name}'" if app_name else "the active window"
        return {"success": True, "message": f"[mock] Would maximize {target}.", "data": None}

    hwnd = _find_window_by_title(app_name) if app_name else _active_window()
    if not hwnd:
        return {"success": False, "message": "No matching window found.", "data": None}

    _user32.ShowWindow(hwnd, SW_MAXIMIZE)
    return {"success": True, "message": f"{'Window' if not app_name else app_name} maximized.", "data": None}


def restore_window(
    app_name: str = "",
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Restore the named window from minimized/maximized state."""
    err = _require_windows("restore_window")
    if err:
        return err

    if mock_mode:
        target = f"'{app_name}'" if app_name else "the active window"
        return {"success": True, "message": f"[mock] Would restore {target}.", "data": None}

    hwnd = _find_window_by_title(app_name) if app_name else _active_window()
    if not hwnd:
        return {"success": False, "message": "No matching window found.", "data": None}

    _user32.ShowWindow(hwnd, SW_RESTORE)
    return {"success": True, "message": f"{'Window' if not app_name else app_name} restored.", "data": None}


def focus_application(
    app_name: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Bring an existing window to the foreground.  Does NOT launch the app."""
    err = _require_windows("focus_application")
    if err:
        return err

    if not app_name or not app_name.strip():
        return {"success": False, "message": "app_name is required.", "data": None}

    if mock_mode:
        return {"success": True, "message": f"[mock] Would focus '{app_name}'.", "data": None}

    hwnd = _find_window_by_title(app_name)
    if hwnd is None:
        return {
            "success": False,
            "message": (
                f"No open window matching '{app_name}' found. "
                "If it isn't open yet, use open_application to launch it first."
            ),
            "data": None,
        }

    # Bring to foreground: restore if minimized, then set foreground.
    _user32.ShowWindow(hwnd, SW_RESTORE)
    _user32.SetForegroundWindow(hwnd)
    logger.info("Focused window: %s (hwnd=%s)", app_name, hwnd)
    return {"success": True, "message": f"{app_name} brought to the foreground.", "data": {"hwnd": hwnd}}
