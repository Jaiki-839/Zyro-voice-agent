"""
tests/test_whatsapp_web.py -- Tests for tools/whatsapp_web.py

All tests use mock_mode=True. No real browser is opened.
No real WhatsApp messages are sent.
"""
import time
import pytest

from core.session import SessionContext
from core.permissions import ConfirmationManager, PermissionLevel, PendingConfirmation, _fingerprint
from core.router import ToolDispatcher, CONFIRMATION_TOKEN_ARG
from core.tool_registry import Tool, ToolParameter, ToolRegistry
from tools.whatsapp_web import (
    open_whatsapp,
    search_whatsapp_contact,
    open_whatsapp_contact,
    send_whatsapp_message,
)


class TestOpenWhatsApp:
    def test_open_whatsapp_mock(self):
        result = open_whatsapp(mock_mode=True)
        assert result["success"] is True
        assert "[mock]" in result["message"]

    def test_open_whatsapp_sets_active_app(self):
        session = SessionContext()
        open_whatsapp(mock_mode=True, session=session)
        assert session.webapp.active_app == "whatsapp"

    def test_open_whatsapp_returns_context(self):
        session = SessionContext()
        result = open_whatsapp(mock_mode=True, session=session)
        assert result["data"]["context"]["active_app"] == "whatsapp"


class TestSearchWhatsAppContact:
    def test_search_contact_mock(self):
        result = search_whatsapp_contact(contact_name="Shlok", mock_mode=True)
        assert result["success"] is True
        assert result["data"]["search_initiated"] is True

    def test_search_empty_name_fails(self):
        result = search_whatsapp_contact(contact_name="", mock_mode=True)
        assert result["success"] is False

    def test_search_name_too_long_fails(self):
        result = search_whatsapp_contact(contact_name="x" * 101, mock_mode=True)
        assert result["success"] is False

    def test_search_reports_needs_selection(self):
        """Search must note that user needs to select from results."""
        result = search_whatsapp_contact(contact_name="John", mock_mode=True)
        assert result["success"] is True
        assert result["data"].get("needs_selection") is True


class TestOpenWhatsAppContact:
    def test_open_contact_mock(self):
        result = open_whatsapp_contact(contact_name="Shlok", mock_mode=True)
        assert result["success"] is True
        assert result["data"]["contact"] == "Shlok"

    def test_open_contact_sets_active_target(self):
        session = SessionContext()
        open_whatsapp_contact(contact_name="Shlok", mock_mode=True, session=session)
        assert session.webapp.active_target == "Shlok"
        assert session.webapp.active_app == "whatsapp"

    def test_empty_contact_fails(self):
        result = open_whatsapp_contact(contact_name="", mock_mode=True)
        assert result["success"] is False


class TestSendWhatsAppMessage:
    def test_send_message_mock(self):
        result = send_whatsapp_message(
            contact_name="Shlok", message="hiii", mock_mode=True
        )
        assert result["success"] is True
        assert "Shlok" in result["message"]
        assert "hiii" in result["message"]

    def test_empty_message_fails(self):
        result = send_whatsapp_message(
            contact_name="Shlok", message="", mock_mode=True
        )
        assert result["success"] is False

    def test_empty_contact_with_no_context_fails(self):
        result = send_whatsapp_message(
            contact_name="", message="hello", mock_mode=True
        )
        assert result["success"] is False

    def test_empty_contact_resolved_from_context(self):
        session = SessionContext()
        session.webapp.update(active_app="whatsapp", active_target="Shlok")
        result = send_whatsapp_message(
            contact_name="", message="hello", mock_mode=True, session=session
        )
        assert result["success"] is True
        assert "Shlok" in result["message"]

    def test_send_updates_last_action(self):
        session = SessionContext()
        send_whatsapp_message(
            contact_name="Shlok", message="hi", mock_mode=True, session=session
        )
        assert session.webapp.last_action == "send_message"

    # ------------------------------------------------------------------
    # CONFIRM permission gate tests -- token fingerprints contact + message
    # ------------------------------------------------------------------

    def _make_dispatcher(self, mock_mode=True):
        registry = ToolRegistry()
        registry.register(Tool(
            name="send_whatsapp_message",
            description="Send WhatsApp message",
            permission=PermissionLevel.CONFIRM,
            handler=send_whatsapp_message,
            parameters=(
                ToolParameter("contact_name", "string", "Contact", required=False, default=""),
                ToolParameter("message", "string", "Message text"),
            ),
        ))
        confirmations = ConfirmationManager()
        dispatcher = ToolDispatcher(
            registry=registry,
            confirmations=confirmations,
            mock_mode=mock_mode,
        )
        return dispatcher, confirmations

    def test_send_without_token_requires_confirmation(self):
        dispatcher, _ = self._make_dispatcher()
        outcome = dispatcher.dispatch(
            "send_whatsapp_message", {"contact_name": "Shlok", "message": "hiii"}
        )
        assert outcome.executed is False
        assert outcome.result["data"]["needs_confirmation"] is True
        assert "confirmation_token" in outcome.result["data"]

    def test_send_with_valid_token_executes(self):
        dispatcher, _ = self._make_dispatcher()
        # Step 1: get token
        outcome1 = dispatcher.dispatch(
            "send_whatsapp_message", {"contact_name": "Shlok", "message": "hiii"}
        )
        token = outcome1.result["data"]["confirmation_token"]
        # Step 2: confirm
        outcome2 = dispatcher.dispatch(
            "send_whatsapp_message",
            {"contact_name": "Shlok", "message": "hiii", CONFIRMATION_TOKEN_ARG: token},
        )
        assert outcome2.executed is True
        assert outcome2.result["success"] is True

    def test_changed_message_invalidates_token(self):
        """Changing message after confirmation token is issued must reject."""
        dispatcher, _ = self._make_dispatcher()
        outcome1 = dispatcher.dispatch(
            "send_whatsapp_message", {"contact_name": "Shlok", "message": "hiii"}
        )
        token = outcome1.result["data"]["confirmation_token"]
        # Use token with DIFFERENT message
        outcome2 = dispatcher.dispatch(
            "send_whatsapp_message",
            {"contact_name": "Shlok", "message": "hello", CONFIRMATION_TOKEN_ARG: token},
        )
        assert outcome2.executed is False

    def test_changed_contact_invalidates_token(self):
        """Changing contact after confirmation token is issued must reject."""
        dispatcher, _ = self._make_dispatcher()
        outcome1 = dispatcher.dispatch(
            "send_whatsapp_message", {"contact_name": "Shlok", "message": "hiii"}
        )
        token = outcome1.result["data"]["confirmation_token"]
        # Use token with DIFFERENT contact
        outcome2 = dispatcher.dispatch(
            "send_whatsapp_message",
            {"contact_name": "Rahul", "message": "hiii", CONFIRMATION_TOKEN_ARG: token},
        )
        assert outcome2.executed is False

    def test_expired_token_rejected(self):
        dispatcher, confirmations = self._make_dispatcher()
        ticket = PendingConfirmation(
            token="old_token",
            tool_name="send_whatsapp_message",
            args_fingerprint=_fingerprint(
                "send_whatsapp_message",
                {"contact_name": "Shlok", "message": "hiii"},
            ),
            created_at=time.time() - 999,
            ttl_seconds=60.0,
        )
        confirmations._pending["old_token"] = ticket
        outcome = dispatcher.dispatch(
            "send_whatsapp_message",
            {"contact_name": "Shlok", "message": "hiii", CONFIRMATION_TOKEN_ARG: "old_token"},
        )
        assert outcome.executed is False

    def test_missing_token_always_blocks(self):
        dispatcher, _ = self._make_dispatcher()
        for _ in range(3):
            outcome = dispatcher.dispatch(
                "send_whatsapp_message", {"contact_name": "Shlok", "message": "hiii"}
            )
            assert outcome.result["data"]["needs_confirmation"] is True

    def test_token_is_one_shot(self):
        """Confirmation token is consumed after first use -- cannot be replayed."""
        dispatcher, _ = self._make_dispatcher()
        outcome1 = dispatcher.dispatch(
            "send_whatsapp_message", {"contact_name": "Shlok", "message": "hiii"}
        )
        token = outcome1.result["data"]["confirmation_token"]
        # First use: succeeds
        outcome2 = dispatcher.dispatch(
            "send_whatsapp_message",
            {"contact_name": "Shlok", "message": "hiii", CONFIRMATION_TOKEN_ARG: token},
        )
        assert outcome2.executed is True
        # Second use of same token: rejected
        outcome3 = dispatcher.dispatch(
            "send_whatsapp_message",
            {"contact_name": "Shlok", "message": "hiii", CONFIRMATION_TOKEN_ARG: token},
        )
        assert outcome3.executed is False
