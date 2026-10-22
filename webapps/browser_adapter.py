"""
webapps/browser_adapter.py -- Controlled browser interaction helpers.

SECURITY MODEL:
  This module exposes ONLY explicitly named, narrowly scoped actions.
  No generic pyautogui.press(user_input), pyautogui.click(x, y), or
  pyautogui.write(arbitrary_string) is ever exposed to tool handlers or Gemini.

  All keyboard shortcuts are fixed constants defined in this module.
  All text typed is passed through app-specific named functions only.

  Gemini NEVER generates raw browser automation instructions.
  All actions are validated by tool handlers before reaching this module.

Available named actions (public API):
  wait_for_browser_ready(title_hint, timeout) -> bool
  focus_browser()                             -> bool
  browser_scroll(direction, amount)           -> bool  [constrained only]
  browser_back()                              -> bool  [Alt+Left only]
  browser_forward()                           -> bool  [Alt+Right only]
  browser_refresh()                           -> bool  [F5 only]
  discord_quick_search(query)                 -> bool  [Ctrl+K + type + Enter]
  discord_type_message(message)               -> bool  [type text, no submit]
  discord_submit_message()                    -> bool  [Enter only -- after CONFIRM]
  whatsapp_search_contact(contact_name)       -> bool  [Ctrl+F + type + wait]
  whatsapp_type_message(message)              -> bool  [type text, no submit]
  whatsapp_submit_message()                   -> bool  [Enter only -- after CONFIRM]
  is_available()                              -> bool

NOT in this module (and must never be added):
  arbitrary pyautogui.press(user_input)
  arbitrary pyautogui.click(x, y)
  arbitrary pyautogui.write(user_input)
  DOM reading, JS injection, CDP automation
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger("zyro.browser_adapter")

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------

_PYAUTOGUI_AVAILABLE = False
_PYGETWINDOW_AVAILABLE = False

try:
    import pyautogui  # type: ignore[import]
    pyautogui.FAILSAFE = True   # move mouse to any corner to abort
    pyautogui.PAUSE = 0.05      # short delay between atomic actions
    _PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None  # type: ignore[assignment]

try:
    import pygetwindow  # type: ignore[import]
    _PYGETWINDOW_AVAILABLE = True
except ImportError:
    pygetwindow = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constrained scroll constants -- the ONLY allowed scroll amounts
# ---------------------------------------------------------------------------

_SCROLL_AMOUNTS: dict[str, int] = {
    "small": 3,
    "medium": 7,
    "large": 15,
}
ALLOWED_SCROLL_AMOUNTS: tuple[str, ...] = ("small", "medium", "large")
ALLOWED_SCROLL_DIRECTIONS: tuple[str, ...] = ("up", "down")

# ---------------------------------------------------------------------------
# Fixed keyboard constants -- NEVER parametrized from outside
# ---------------------------------------------------------------------------

_KEY_ENTER = "enter"
_KEY_F5 = "f5"
_KEY_ESCAPE = "escape"
_SHORTCUT_BROWSER_ADDRESS = ("ctrl", "l")   # focus address bar
_SHORTCUT_BACK = ("alt", "left")             # browser back
_SHORTCUT_FORWARD = ("alt", "right")         # browser forward
_SHORTCUT_SELECT_ALL = ("ctrl", "a")

# Discord
_SHORTCUT_DISCORD_SEARCH = ("ctrl", "k")    # Discord quick search

# WhatsApp
_SHORTCUT_WHATSAPP_SEARCH = ("ctrl", "f")   # WhatsApp search panel

# ---------------------------------------------------------------------------
# Internal helpers -- NOT part of the public API, never parametrized externally
# ---------------------------------------------------------------------------

def _hotkey(*keys: str) -> None:
    """Press a fixed hotkey combination. Arguments are compile-time constants only."""
    pyautogui.hotkey(*keys)
    time.sleep(0.12)


def _press(key: str) -> None:
    """Press a single fixed key. key must be a compile-time constant."""
    pyautogui.press(key)
    time.sleep(0.06)


def _type_text(text: str) -> None:
    """
    Type text using pyautogui.write().

    text is typed character-by-character as literal characters.
    It is NOT interpreted as a key sequence. Safe for user-provided strings.
    Only called from named app-specific functions -- never exposed directly.
    """
    pyautogui.write(text, interval=0.04)


# ---------------------------------------------------------------------------
# Public: availability check
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Return True if pyautogui is installed and keyboard automation is ready."""
    return _PYAUTOGUI_AVAILABLE


# ---------------------------------------------------------------------------
# Public: browser window detection
# ---------------------------------------------------------------------------

def wait_for_browser_ready(title_hint: str, timeout: float = 8.0) -> bool:
    """
    Poll for a browser window whose title contains title_hint.

    Returns True if found within timeout seconds, False otherwise.
    Falls back to a fixed 2-second delay if pygetwindow is not installed.
    """
    if not _PYGETWINDOW_AVAILABLE:
        logger.warning(
            "pygetwindow not installed -- assuming browser ready after 2s delay. "
            "pip install pygetwindow for reliable readiness detection."
        )
        time.sleep(2.0)
        return True

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            windows = pygetwindow.getWindowsWithTitle(title_hint)
            if windows:
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.35)
    return False


def focus_browser() -> bool:
    """
    Bring the frontmost browser window to the foreground.
    Tries Chrome, Edge, Firefox, Brave, Opera in order.
    Returns True if a window was found and activated.
    """
    if not _PYGETWINDOW_AVAILABLE:
        return False

    for hint in ("Chrome", "Edge", "Firefox", "Brave", "Opera"):
        try:
            wins = pygetwindow.getWindowsWithTitle(hint)
            if wins:
                wins[0].activate()
                time.sleep(0.35)
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


# ---------------------------------------------------------------------------
# Public: generic navigation (fixed keys only)
# ---------------------------------------------------------------------------

def browser_back() -> bool:
    """Alt+Left -- browser back. Returns True on success."""
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _hotkey(*_SHORTCUT_BACK)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("browser_back failed: %s", exc)
        return False


def browser_forward() -> bool:
    """Alt+Right -- browser forward. Returns True on success."""
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _hotkey(*_SHORTCUT_FORWARD)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("browser_forward failed: %s", exc)
        return False


def browser_refresh() -> bool:
    """F5 -- browser refresh. Returns True on success."""
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _press(_KEY_F5)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("browser_refresh failed: %s", exc)
        return False


def browser_scroll(direction: str, amount: str) -> bool:
    """
    Scroll the focused browser window.

    direction must be "up" or "down".
    amount must be "small", "medium", or "large".

    Only the three constrained scroll amounts are allowed.
    No arbitrary scroll values can be passed.
    Returns True on success.
    """
    if not _PYAUTOGUI_AVAILABLE:
        return False

    if direction not in ALLOWED_SCROLL_DIRECTIONS:
        logger.warning("browser_scroll: invalid direction %r (must be 'up' or 'down')", direction)
        return False

    clicks = _SCROLL_AMOUNTS.get(amount)
    if clicks is None:
        logger.warning("browser_scroll: invalid amount %r (must be 'small', 'medium', or 'large')", amount)
        return False

    # pyautogui.scroll: positive = scroll up, negative = scroll down
    scroll_value = clicks if direction == "up" else -clicks
    try:
        pyautogui.scroll(scroll_value)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("browser_scroll failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Public: Discord named actions
# ---------------------------------------------------------------------------

def discord_quick_search(query: str) -> bool:
    """
    Open Discord's quick-search panel (Ctrl+K), type a query, and submit (Enter).

    query: the server, channel, or user to search for.
    This is a named, explicit action -- not a generic keyboard injection.
    Returns True if the keyboard sequence was sent successfully.
    """
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _hotkey(*_SHORTCUT_DISCORD_SEARCH)   # Ctrl+K: open quick search
        time.sleep(0.45)                      # wait for search panel
        _hotkey(*_SHORTCUT_SELECT_ALL)        # clear any existing text
        _type_text(query)                     # type the search query (literal chars)
        time.sleep(0.3)
        _press(_KEY_ENTER)                    # select first result
        time.sleep(0.25)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("discord_quick_search(%r) failed: %s", query, exc)
        return False


def discord_type_message(message: str) -> bool:
    """
    Type a message into Discord's message input box WITHOUT submitting.

    This only types -- it does NOT press Enter.
    Submission requires an explicit call to discord_submit_message(),
    which must only be called after the CONFIRM permission gate passes.
    Returns True on success.
    """
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _type_text(message)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("discord_type_message failed: %s", exc)
        return False


def discord_submit_message() -> bool:
    """
    Submit the typed Discord message by pressing Enter.

    ONLY call this AFTER the CONFIRM permission gate has been cleared by
    the ToolDispatcher. Never call this speculatively.
    Returns True on success.
    """
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _press(_KEY_ENTER)
        time.sleep(0.2)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("discord_submit_message failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Public: WhatsApp named actions
# ---------------------------------------------------------------------------

def whatsapp_search_contact(contact_name: str) -> bool:
    """
    Open WhatsApp Web's search panel (Ctrl+F) and type a contact name.

    The user must then select the correct match (we do not auto-click results
    because contact names can be ambiguous and we must not guess).
    Returns True if the sequence was sent successfully.
    """
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _hotkey(*_SHORTCUT_WHATSAPP_SEARCH)  # Ctrl+F: open search
        time.sleep(0.45)                      # wait for search input
        _hotkey(*_SHORTCUT_SELECT_ALL)
        _type_text(contact_name)              # type contact name (literal chars)
        time.sleep(0.4)                       # let results appear
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("whatsapp_search_contact(%r) failed: %s", contact_name, exc)
        return False


def whatsapp_open_first_result() -> bool:
    """
    Press Enter to open the first WhatsApp search result.

    Only call after whatsapp_search_contact() has been called and exactly
    ONE unambiguous match is expected. Returns True on success.
    """
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _press(_KEY_ENTER)
        time.sleep(0.3)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("whatsapp_open_first_result failed: %s", exc)
        return False


def whatsapp_type_message(message: str) -> bool:
    """
    Type a message into WhatsApp Web's message input WITHOUT submitting.

    Does NOT press Enter. Submission requires whatsapp_submit_message()
    which must only be called after the CONFIRM permission gate passes.
    Returns True on success.
    """
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _type_text(message)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("whatsapp_type_message failed: %s", exc)
        return False


def whatsapp_submit_message() -> bool:
    """
    Submit the typed WhatsApp message by pressing Enter.

    ONLY call this AFTER the CONFIRM permission gate has been cleared.
    Never call this speculatively or before user confirmation.
    Returns True on success.
    """
    if not _PYAUTOGUI_AVAILABLE:
        return False
    try:
        _press(_KEY_ENTER)
        time.sleep(0.2)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("whatsapp_submit_message failed: %s", exc)
        return False
