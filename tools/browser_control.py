"""
tools/browser_control.py -- Browser tab control via keyboard shortcuts.

All actions send a single, hardcoded key combination to the foreground window.
No arbitrary key injection.  Only 6 specific combos are possible:

  Ctrl+Tab        next tab
  Ctrl+Shift+Tab  previous tab
  Ctrl+W          close tab
  Ctrl+T          new tab
  Ctrl+1..8       switch to tab N
  Ctrl+9          switch to last tab

The tool does NOT know which tabs are open, what their titles are, or how many
there are -- it sends the browser shortcut and trusts the browser to handle it.
"""
from __future__ import annotations

import ctypes
import logging
import sys
import time
from typing import Any

logger = logging.getLogger("zyro.browser")

if sys.platform == "win32":
    _user32 = ctypes.windll.user32  # type: ignore[attr-defined]
else:
    _user32 = None  # type: ignore[assignment]

# Virtual key codes
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_TAB = 0x09
VK_W = 0x57
VK_T = 0x54
# Digit keys 1-9
_DIGIT_VK = {i: 0x30 + i for i in range(1, 10)}  # 0x31 = '1' ... 0x39 = '9'

KEYEVENTF_KEYUP = 0x0002
_KEY_DELAY = 0.03  # seconds between press and release


def _require_windows(name: str) -> dict[str, Any] | None:
    if sys.platform != "win32" or _user32 is None:
        return {"success": False, "message": f"'{name}' is only available on Windows.", "data": None}
    return None


def _press(*keys: int) -> None:
    """Press all keys in order, then release in reverse order."""
    for k in keys:
        _user32.keybd_event(k, 0, 0, 0)
    time.sleep(_KEY_DELAY)
    for k in reversed(keys):
        _user32.keybd_event(k, 0, KEYEVENTF_KEYUP, 0)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def next_browser_tab(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Switch to the next browser tab (Ctrl+Tab)."""
    err = _require_windows("next_browser_tab")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send Ctrl+Tab (next tab).", "data": None}
    _press(VK_CONTROL, VK_TAB)
    logger.info("Ctrl+Tab sent (next_browser_tab)")
    return {"success": True, "message": "Switched to the next browser tab.", "data": None}


def previous_browser_tab(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Switch to the previous browser tab (Ctrl+Shift+Tab)."""
    err = _require_windows("previous_browser_tab")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send Ctrl+Shift+Tab (previous tab).", "data": None}
    _press(VK_CONTROL, VK_SHIFT, VK_TAB)
    logger.info("Ctrl+Shift+Tab sent (previous_browser_tab)")
    return {"success": True, "message": "Switched to the previous browser tab.", "data": None}


def close_browser_tab(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Close the current browser tab (Ctrl+W)."""
    err = _require_windows("close_browser_tab")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send Ctrl+W (close tab).", "data": None}
    _press(VK_CONTROL, VK_W)
    logger.info("Ctrl+W sent (close_browser_tab)")
    return {"success": True, "message": "Closed the current browser tab.", "data": None}


def open_new_browser_tab(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Open a new browser tab (Ctrl+T)."""
    err = _require_windows("open_new_browser_tab")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send Ctrl+T (new tab).", "data": None}
    _press(VK_CONTROL, VK_T)
    logger.info("Ctrl+T sent (open_new_browser_tab)")
    return {"success": True, "message": "Opened a new browser tab.", "data": None}


def switch_to_browser_tab(
    tab_number: int,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Switch to a specific browser tab by number (1-9).

    Tab 1-8 use Ctrl+1..Ctrl+8.
    Tab 9 (or 'last') uses Ctrl+9, which most browsers treat as 'last tab'.
    Numbers outside 1-9 are rejected.
    """
    err = _require_windows("switch_to_browser_tab")
    if err:
        return err

    if not isinstance(tab_number, int) or tab_number < 1 or tab_number > 9:
        return {
            "success": False,
            "message": f"tab_number must be between 1 and 9, got {tab_number!r}.",
            "data": None,
        }

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would send Ctrl+{tab_number} (switch to tab {tab_number}).",
            "data": None,
        }

    vk_digit = _DIGIT_VK[tab_number]
    _press(VK_CONTROL, vk_digit)
    label = "last tab" if tab_number == 9 else f"tab {tab_number}"
    logger.info("Ctrl+%d sent (switch_to_browser_tab=%d)", tab_number, tab_number)
    return {"success": True, "message": f"Switched to {label}.", "data": {"tab_number": tab_number}}
