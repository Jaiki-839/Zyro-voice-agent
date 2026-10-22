"""
tests/test_discord_web.py -- Tests for tools/discord_web.py

All tests use mock_mode=True. No real browser is opened.
No real Discord messages are sent.
"""
import pytest
from unittest.mock import patch, MagicMock

from core.session import SessionContext
from core.permissions import ConfirmationManager, PermissionLevel
from core.router import ToolDispatcher, CONFIRMATION_TOKEN_ARG
from core.tool_registry import Tool, ToolParameter, ToolRegistry
from tools.discord_web import (
    open_discord,
    open_discord_server,
    open_discord_channel,
    search_discord,
    send_discord_message,
)


class TestOpenDiscord:
    def test_open_discord_mock_success(self):
        result = open_discord(mock_mode=True)
        assert result["success"] is True
        assert "[mock]" in result["message"]

    def test_open_discord_sets_active_app(self):
        session = SessionContext()
        open_discord(mock_mode=True, session=session)
        assert session.webapp.active_app == "discord"

    def test_open_discord_clears_previous_target(self):
        session = SessionContext()
        session.webapp.update(active_app="instagram", active_target="xyz")
        open_discord(mock_mode=True, session=session)
        assert session.webapp.active_app == "discord"
        assert session.webapp.active_target is None

    def test_open_discord_returns_context_in_data(self):
        session = SessionContext()
        result = open_discord(mock_mode=True, session=session)
        assert result["data"]["context"]["active_app"] == "discord"


class TestOpenDiscordServer:
    def test_navigate_to_server_mock(self):
        result = open_discord_server(server_name="Gaming", mock_mode=True)
        assert result["success"] is True
        assert "Gaming" in result["message"] or "Gaming" in str(result["data"])

    def test_empty_server_name_fails(self):
        result = open_discord_server(server_name="", mock_mode=True)
        assert result["success"] is False

    def test_server_name_too_long_fails(self):
        result = open_discord_server(server_name="x" * 101, mock_mode=True)
        assert result["success"] is False

    def test_server_sets_context(self):
        session = SessionContext()
        open_discord_server(server_name="Gaming", mock_mode=True, session=session)
        assert session.webapp.active_target == "Gaming"
        assert session.webapp.active_app == "discord"


class TestOpenDiscordChannel:
    def test_navigate_to_channel_mock(self):
        result = open_discord_channel(channel_name="general", mock_mode=True)
        assert result["success"] is True

    def test_empty_channel_fails(self):
        result = open_discord_channel(channel_name="", mock_mode=True)
        assert result["success"] is False

    def test_channel_updates_context_page(self):
        session = SessionContext()
        open_discord_channel(channel_name="general", mock_mode=True, session=session)
        assert "general" in (session.webapp.active_page or "")


class TestSearchDiscord:
    def test_search_discord_mock(self):
        result = search_discord(query="Shlok", mock_mode=True)
        assert result["success"] is True

    def test_empty_query_fails(self):
        result = search_discord(query="", mock_mode=True)
        assert result["success"] is False


class TestSendDiscordMessage:
    def test_send_discord_message_mock(self):
        """Mock mode: bypass CONFIRM gate, handler executes directly."""
        result = send_discord_message(message="hello", mock_mode=True)
        assert result["success"] is True
        assert "[mock]" in result["message"]
        assert "hello" in result["message"]

    def test_empty_message_fails(self):
        result = send_discord_message(message="", mock_mode=True)
        assert result["success"] is False

    def test_message_too_long_fails(self):
        result = send_discord_message(message="x" * 2001, mock_mode=True)
        assert result["success"] is False

    def test_send_updates_last_action(self):
        session = SessionContext()
        session.webapp.switch_app("discord")
        send_discord_message(message="hi", mock_mode=True, session=session)
        assert session.webapp.last_action == "send_message"

    # -----------------------------------------------------------------
    # CONFIRM permission gate tests via ToolDispatcher
    # -----------------------------------------------------------------

    def _make_registry_and_dispatcher(self, mock_mode=True):
        registry = ToolRegistry()
        registry.register(Tool(
            name="send_discord_message",
            description="Send Discord message",
            permission=PermissionLevel.CONFIRM,
            handler=send_discord_message,
            parameters=(
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

    def test_send_without_confirmation_returns_needs_confirmation(self):
        dispatcher, _ = self._make_registry_and_dispatcher()
        outcome = dispatcher.dispatch("send_discord_message", {"message": "hiii"})
        assert outcome.executed is False
        assert outcome.result["data"]["needs_confirmation"] is True
        assert "confirmation_token" in outcome.result["data"]

    def test_send_with_valid_token_executes(self):
        dispatcher, confirmations = self._make_registry_and_dispatcher()
        # First call: get token
        outcome1 = dispatcher.dispatch("send_discord_message", {"message": "hiii"})
        token = outcome1.result["data"]["confirmation_token"]
        # Second call: supply token
        outcome2 = dispatcher.dispatch(
            "send_discord_message",
            {"message": "hiii", CONFIRMATION_TOKEN_ARG: token},
        )
        assert outcome2.executed is True
        assert outcome2.result["success"] is True

    def test_changed_message_invalidates_token(self):
        """Changing the message after getting a token must cause rejection."""
        dispatcher, confirmations = self._make_registry_and_dispatcher()
        # Get token for "hiii"
        outcome1 = dispatcher.dispatch("send_discord_message", {"message": "hiii"})
        token = outcome1.result["data"]["confirmation_token"]
        # Attempt with different message "hello" using the token for "hiii"
        outcome2 = dispatcher.dispatch(
            "send_discord_message",
            {"message": "hello", CONFIRMATION_TOKEN_ARG: token},
        )
        assert outcome2.executed is False

    def test_stale_token_rejected_after_expiry(self):
        """An expired token must be rejected."""
        import time
        from core.permissions import PendingConfirmation
        dispatcher, confirmations = self._make_registry_and_dispatcher()
        # Manually insert an expired ticket
        from core.permissions import _fingerprint
        ticket = PendingConfirmation(
            token="expired_tok",
            tool_name="send_discord_message",
            args_fingerprint=_fingerprint("send_discord_message", {"message": "hi"}),
            created_at=time.time() - 999,  # way in the past
            ttl_seconds=60.0,
        )
        confirmations._pending["expired_tok"] = ticket
        outcome = dispatcher.dispatch(
            "send_discord_message",
            {"message": "hi", CONFIRMATION_TOKEN_ARG: "expired_tok"},
        )
        assert outcome.executed is False

    def test_missing_token_always_requires_confirmation(self):
        dispatcher, _ = self._make_registry_and_dispatcher()
        for _ in range(3):
            outcome = dispatcher.dispatch("send_discord_message", {"message": "hello"})
            assert outcome.result["data"]["needs_confirmation"] is True
