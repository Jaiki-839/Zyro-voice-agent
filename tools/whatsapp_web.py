"""
tools/whatsapp_web.py -- WhatsApp Web tools for ZYRO.

Interaction strategy:
  - Open WhatsApp Web via controlled URL (web.whatsapp.com).
  - Contact search uses Ctrl+F (WhatsApp search shortcut) via browser_adapter.whatsapp_search_contact().
  - Message sending is a CONFIRM-level action requiring explicit user confirmation.
  - The CONFIRM token is fingerprinted to (tool, contact_name, message) so that
    changing either the target OR the message invalidates the token.

Security:
  - No arbitrary keyboard sequences.
  - No DOM access, JS injection, or CDP.
  - whatsapp_search_contact() is the ONLY search keyboard automation exposed.
  - whatsapp_type_message() and whatsapp_submit_message() are only called after CONFIRM.
  - ZYRO never guesses when multiple contacts match.
  - ZYRO never claims success if it cannot verify the action.

Tool result convention: {success: bool, message: str, data: dict | None}
"""
from __future__ import annotations

import logging
import webbrowser
from typing import Any

from webapps.browser_adapter import (
    focus_browser,
    is_available,
    wait_for_browser_ready,
    whatsapp_open_first_result,
    whatsapp_search_contact,
    whatsapp_submit_message,
    whatsapp_type_message,
)
from webapps.registry import WEB_APP_REGISTRY

logger = logging.getLogger("zyro.tools.whatsapp")

_APP = WEB_APP_REGISTRY["whatsapp"]
_OPEN_TIMEOUT = 12.0  # WhatsApp Web can be slow loading QR code


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


def open_whatsapp(mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """Open WhatsApp Web in the default browser."""
    if mock_mode:
        if session is not None:
            session.webapp.switch_app("whatsapp")
        return _result(
            True,
            "[mock] Would open WhatsApp Web. WhatsApp is open. What would you like me to do?",
            {"app": "whatsapp", "ready": True,
             "context": session.webapp.to_dict() if session else {}},
        )

    webbrowser.open(_APP.base_url)
    ready = wait_for_browser_ready("WhatsApp", timeout=_OPEN_TIMEOUT)

    if session is not None:
        session.webapp.switch_app("whatsapp")

    if not ready:
        return _result(
            True,
            "WhatsApp Web opened, but the readiness check timed out. "
            "If this is your first time, you may need to scan the QR code to log in.",
            {"app": "whatsapp", "ready": False,
             "context": session.webapp.to_dict() if session else {}},
        )

    return _result(
        True,
        "WhatsApp Web is open. What would you like me to do?",
        {"app": "whatsapp", "ready": True,
         "context": session.webapp.to_dict() if session else {}},
    )


def search_whatsapp_contact(contact_name: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Search for a WhatsApp contact using Ctrl+F (WhatsApp search shortcut).

    Opens the WhatsApp search panel and types the contact name.
    Does NOT automatically select the first result (to avoid guessing when
    multiple contacts match). Gemini will ask the user if there's ambiguity.
    """
    ok, val = _validate_text(contact_name, "Contact name", max_len=100)
    if not ok:
        return _result(False, val, None)

    if mock_mode:
        if session is not None:
            session.webapp.update(
                active_app="whatsapp", last_action="search_contact",
            )
        return _result(
            True,
            f"[mock] Would search WhatsApp for contact '{val}'.",
            {"contact": val, "search_initiated": True, "needs_selection": True,
             "context": session.webapp.to_dict() if session else {}},
        )

    if not is_available():
        return _result(
            False,
            "WhatsApp contact search requires pyautogui. pip install pyautogui pygetwindow",
            None,
        )

    focused = focus_browser()
    if not focused:
        logger.warning("Could not confirm browser focused for WhatsApp search")

    sent = whatsapp_search_contact(val)
    if not sent:
        return _result(
            False,
            f"Couldn't open WhatsApp search for '{val}'. "
            "Make sure WhatsApp Web is open and you are logged in.",
            None,
        )

    if session is not None:
        session.webapp.update(active_app="whatsapp", last_action="search_contact")

    return _result(
        True,
        f"Searched WhatsApp for '{val}'. "
        "If multiple results appear, please tell me which one to select.",
        {"contact": val, "search_initiated": True,
         "needs_selection": True,
         "context": session.webapp.to_dict() if session else {}},
    )


def open_whatsapp_contact(contact_name: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Search for a WhatsApp contact and open the first result.

    Use this only when the contact name is unambiguous.
    If the user says the target is ambiguous, use search_whatsapp_contact instead.
    """
    ok, val = _validate_text(contact_name, "Contact name", max_len=100)
    if not ok:
        return _result(False, val, None)

    if mock_mode:
        if session is not None:
            session.webapp.update(
                active_app="whatsapp", active_target=val, last_action="open_contact",
            )
        return _result(
            True,
            f"[mock] Would open WhatsApp contact '{val}'.",
            {"contact": val, "context": session.webapp.to_dict() if session else {}},
        )

    if not is_available():
        return _result(
            False,
            "Opening WhatsApp contacts requires pyautogui. pip install pyautogui pygetwindow",
            None,
        )

    focused = focus_browser()
    if not focused:
        logger.warning("Could not confirm browser focused for WhatsApp open contact")

    searched = whatsapp_search_contact(val)
    if not searched:
        return _result(
            False,
            f"Couldn't search WhatsApp for '{val}'. "
            "Make sure WhatsApp Web is open and you are logged in.",
            None,
        )

    # Open the first search result
    opened = whatsapp_open_first_result()
    if not opened:
        return _result(
            False,
            f"Found search results for '{val}' but couldn't open the contact. "
            "If multiple contacts match, please specify which one.",
            None,
        )

    if session is not None:
        session.webapp.update(
            active_app="whatsapp", active_target=val, last_action="open_contact",
        )

    return _result(
        True,
        f"Opened WhatsApp contact '{val}'.",
        {"contact": val, "context": session.webapp.to_dict() if session else {}},
    )


def send_whatsapp_message(
    contact_name: str = "",
    message: str = "",
    mock_mode: bool = False,
    session=None,
    **_,
) -> dict[str, Any]:
    """
    Send a WhatsApp message to a contact.

    PERMISSION: CONFIRM -- the ToolDispatcher requires explicit user confirmation.
    The CONFIRM token fingerprints (tool, contact_name, message), so:
      - Changing the contact_name invalidates the token.
      - Changing the message text invalidates the token.
      - An expired token is rejected.
      - A missing token triggers a new confirmation request.

    This handler is only invoked after the user has explicitly confirmed via
    the confirmation flow in core/router.py. Gemini never bypasses this gate.
    """
    ok_c, contact_val = _validate_text(contact_name, "Contact name", max_len=100)
    if not ok_c:
        # Try to resolve from context
        if session is not None and session.webapp.active_target:
            contact_val = session.webapp.active_target
        else:
            return _result(False, contact_val, None)

    ok_m, message_val = _validate_text(message, "Message", max_len=2000)
    if not ok_m:
        return _result(False, message_val, None)

    if mock_mode:
        if session is not None:
            session.webapp.update(
                active_app="whatsapp", active_target=contact_val, last_action="send_message",
            )
        return _result(
            True,
            f"[mock] Would send '{message_val}' to {contact_val} on WhatsApp.",
            {"contact": contact_val, "message": message_val,
             "context": session.webapp.to_dict() if session else {}},
        )

    if not is_available():
        return _result(
            False,
            "Sending WhatsApp messages requires pyautogui. pip install pyautogui pygetwindow",
            None,
        )

    focused = focus_browser()
    if not focused:
        logger.warning("Could not confirm browser focused for WhatsApp message send")

    # Open the contact first if not already active
    current_target = session.webapp.active_target if session else None
    if not current_target or current_target.lower() != contact_val.lower():
        searched = whatsapp_search_contact(contact_val)
        if not searched:
            return _result(
                False,
                f"Couldn't find WhatsApp contact '{contact_val}'. "
                "Make sure WhatsApp Web is open and you are logged in.",
                None,
            )
        opened = whatsapp_open_first_result()
        if not opened:
            return _result(
                False,
                f"Found search results for '{contact_val}' but couldn't open the contact. "
                "If multiple contacts match, please tell me which one.",
                None,
            )

    # Type the message (no Enter yet)
    typed = whatsapp_type_message(message_val)
    if not typed:
        return _result(
            False,
            f"Couldn't type the message for {contact_val}. "
            "Make sure the WhatsApp message box is focused.",
            None,
        )

    # Submit (Enter) -- only reached after CONFIRM gate
    submitted = whatsapp_submit_message()
    if not submitted:
        return _result(
            False,
            f"Message was typed but couldn't be submitted to {contact_val}.",
            None,
        )

    if session is not None:
        session.webapp.update(
            active_app="whatsapp", active_target=contact_val, last_action="send_message",
        )

    return _result(
        True,
        f"Sent '{message_val}' to {contact_val} on WhatsApp.",
        {"contact": contact_val, "message": message_val,
         "context": session.webapp.to_dict() if session else {}},
    )
