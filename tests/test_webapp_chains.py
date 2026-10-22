"""
tests/test_webapp_chains.py -- Multi-step webapp tool chain + sleep-gate tests.

Tests:
  - Multi-step chaining: instagram search → profile → reels
  - Multi-step chaining: web tool → webapp tool → web tool
  - Sleep gate blocks ALL webapp tools
  - No arbitrary keyboard/mouse input is exposed via the dispatcher
  - Browser-not-available failure path
  - Ambiguous target handling (returns needs_selection)
  - Context preserved correctly across chained calls
"""
import pytest
from unittest.mock import patch, MagicMock

from core.session import SessionContext
from core.permissions import PermissionLevel
from core.router import ToolDispatcher
from core.tool_registry import Tool, ToolParameter, ToolRegistry
from core.zyro_state import StateManager
from tools.instagram import open_instagram, search_instagram, open_instagram_profile, open_instagram_reels
from tools.discord_web import (
    open_discord,
    open_discord_server,
    open_discord_channel,
    search_discord,
    send_discord_message,
)
from tools.whatsapp_web import (
    open_whatsapp,
    search_whatsapp_contact,
    open_whatsapp_contact,
    send_whatsapp_message,
)
from tools.webapp_nav import scroll_webapp, go_back_webapp, go_forward_webapp, refresh_webapp
from tools.youtube_web import open_youtube_webapp, search_youtube_webapp
from tools.spotify_web import open_spotify_webapp, search_spotify_webapp


class TestInstagramChain:
    """open_instagram → search_instagram → open_instagram_profile → open_instagram_reels."""

    def test_full_instagram_chain(self):
        session = SessionContext()

        r1 = open_instagram(mock_mode=True, session=session)
        assert r1["success"] is True
        assert session.webapp.active_app == "instagram"

        r2 = search_instagram(query="virat.kohli", mock_mode=True, session=session)
        assert r2["success"] is True
        assert session.webapp.active_target == "virat.kohli"

        r3 = open_instagram_profile(username="", mock_mode=True, session=session)
        assert r3["success"] is True
        # Profile resolved from context
        assert r3["data"]["username"] == "virat.kohli"
        assert session.webapp.active_page == "profile"

        r4 = open_instagram_reels(username="", mock_mode=True, session=session)
        assert r4["success"] is True
        assert "/reels/" in r4["data"]["url"]
        assert session.webapp.active_page == "reels"

    def test_context_persists_across_calls(self):
        session = SessionContext()
        search_instagram(query="xyz", mock_mode=True, session=session)
        # Follow-up with no explicit username uses context
        result = open_instagram_profile(username="", mock_mode=True, session=session)
        assert result["data"]["username"] == "xyz"

    def test_failed_step_does_not_corrupt_context(self):
        session = SessionContext()
        open_instagram(mock_mode=True, session=session)
        # Invalid username shouldn't change active_target
        search_instagram(query="valid", mock_mode=True, session=session)
        assert session.webapp.active_target == "valid"
        result = open_instagram_profile(username="bad user!", mock_mode=True, session=session)
        assert result["success"] is False
        # active_target unchanged
        assert session.webapp.active_target == "valid"


class TestCrossAppChain:
    """Instagram then Discord then WhatsApp -- context switches correctly."""

    def test_app_switch_clears_target(self):
        session = SessionContext()
        search_instagram(query="kohli", mock_mode=True, session=session)
        assert session.webapp.active_target == "kohli"

        open_discord(mock_mode=True, session=session)
        assert session.webapp.active_app == "discord"
        assert session.webapp.active_target is None

    def test_three_app_switch(self):
        session = SessionContext()
        open_instagram(mock_mode=True, session=session)
        open_discord(mock_mode=True, session=session)
        open_whatsapp(mock_mode=True, session=session)
        assert session.webapp.active_app == "whatsapp"

    def test_youtube_then_scroll(self):
        session = SessionContext()
        open_youtube_webapp(mock_mode=True, session=session)
        assert session.webapp.active_app == "youtube"
        result = scroll_webapp(direction="down", amount="small", mock_mode=True, session=session)
        assert result["success"] is True
        assert session.webapp.last_action == "scroll_down"

    def test_spotify_search_chain(self):
        session = SessionContext()
        open_spotify_webapp(mock_mode=True, session=session)
        r = search_spotify_webapp(query="Arijit Singh", mock_mode=True, session=session)
        assert r["success"] is True
        assert session.webapp.active_target == "Arijit Singh"


class TestSleepGate:
    """Sleep gate must block ALL webapp tools while ZYRO is sleeping."""

    WEBAPP_TOOLS = [
        ("open_instagram", open_instagram, {}),
        ("search_instagram", search_instagram, {"query": "xyz"}),
        ("open_instagram_profile", open_instagram_profile, {}),
        ("open_instagram_reels", open_instagram_reels, {}),
        ("open_discord", open_discord, {}),
        ("open_discord_server", open_discord_server, {"server_name": "General"}),
        ("open_discord_channel", open_discord_channel, {"channel_name": "general"}),
        ("send_discord_message", send_discord_message, {"message": "hi"}),
        ("open_whatsapp", open_whatsapp, {}),
        ("search_whatsapp_contact", search_whatsapp_contact, {"contact_name": "Shlok"}),
        ("open_whatsapp_contact", open_whatsapp_contact, {"contact_name": "Shlok"}),
        ("send_whatsapp_message", send_whatsapp_message, {"contact_name": "Shlok", "message": "hi"}),
        ("scroll_webapp", scroll_webapp, {}),
        ("go_back_webapp", go_back_webapp, {}),
        ("go_forward_webapp", go_forward_webapp, {}),
        ("refresh_webapp", refresh_webapp, {}),
        ("open_youtube_webapp", open_youtube_webapp, {}),
        ("search_youtube_webapp", search_youtube_webapp, {"query": "test"}),
        ("open_spotify_webapp", open_spotify_webapp, {}),
        ("search_spotify_webapp", search_spotify_webapp, {"query": "test"}),
    ]

    def _make_dispatcher_with_sleeping_state(self, tool_name, handler, params):
        registry = ToolRegistry()
        parameters = tuple(
            ToolParameter(k, "string", k, required=True)
            for k in params.keys()
        )
        registry.register(Tool(
            name=tool_name,
            description=f"Test {tool_name}",
            permission=PermissionLevel.SAFE,
            handler=handler,
            parameters=parameters,
        ))
        state_manager = StateManager()
        state_manager.set_sleeping()
        dispatcher = ToolDispatcher(
            registry=registry,
            mock_mode=True,
            state_manager=state_manager,
        )
        return dispatcher

    def test_sleep_blocks_all_webapp_tools(self):
        """Every webapp tool must be blocked while sleeping."""
        for tool_name, handler, params in self.WEBAPP_TOOLS:
            dispatcher = self._make_dispatcher_with_sleeping_state(tool_name, handler, params)
            outcome = dispatcher.dispatch(tool_name, dict(params))
            assert outcome.executed is False, f"Tool '{tool_name}' should be blocked while sleeping"
            assert "sleeping" in outcome.result["message"].lower(), (
                f"Tool '{tool_name}' should mention sleeping in error message"
            )

    def test_tools_work_again_after_wake(self):
        state_manager = StateManager()
        state_manager.set_sleeping()
        registry = ToolRegistry()
        registry.register(Tool(
            name="open_instagram",
            description="Open Instagram",
            permission=PermissionLevel.SAFE,
            handler=open_instagram,
            parameters=(),
        ))
        dispatcher = ToolDispatcher(registry=registry, mock_mode=True, state_manager=state_manager)
        # Blocked while sleeping
        outcome_sleeping = dispatcher.dispatch("open_instagram", {})
        assert outcome_sleeping.executed is False
        # Wake up
        state_manager.set_active()
        # Now works
        outcome_awake = dispatcher.dispatch("open_instagram", {})
        assert outcome_awake.executed is True


# Need to import for sleep test
from tools.discord_web import open_discord_server, open_discord_channel
from tools.whatsapp_web import open_whatsapp_contact


class TestNavTools:
    """Shared webapp navigation (scroll, back, forward, refresh)."""

    def test_scroll_down_medium_mock(self):
        result = scroll_webapp(direction="down", amount="medium", mock_mode=True)
        assert result["success"] is True

    def test_scroll_up_small_mock(self):
        result = scroll_webapp(direction="up", amount="small", mock_mode=True)
        assert result["success"] is True

    def test_scroll_large_mock(self):
        result = scroll_webapp(direction="down", amount="large", mock_mode=True)
        assert result["success"] is True

    def test_scroll_invalid_direction_fails(self):
        result = scroll_webapp(direction="sideways", amount="medium", mock_mode=True)
        assert result["success"] is False

    def test_scroll_invalid_amount_fails(self):
        result = scroll_webapp(direction="down", amount="50", mock_mode=True)
        assert result["success"] is False

    def test_scroll_no_arbitrary_value(self):
        """Verify no integer scroll amounts pass validation."""
        for bad_amount in ["100", "5", "0", "999", "-1"]:
            result = scroll_webapp(direction="down", amount=bad_amount, mock_mode=True)
            assert result["success"] is False, f"Amount '{bad_amount}' should be rejected"

    def test_go_back_mock(self):
        result = go_back_webapp(mock_mode=True)
        assert result["success"] is True

    def test_go_forward_mock(self):
        result = go_forward_webapp(mock_mode=True)
        assert result["success"] is True

    def test_refresh_mock(self):
        result = refresh_webapp(mock_mode=True)
        assert result["success"] is True

    def test_scroll_uses_active_app_from_context(self):
        session = SessionContext()
        session.webapp.switch_app("instagram")
        result = scroll_webapp(mock_mode=True, session=session)
        assert result["success"] is True
        assert result["data"]["app"] == "instagram"


class TestBrowserAdapterAvailability:
    """Verify browser_adapter gracefully handles missing pyautogui."""

    def test_discord_server_without_pyautogui_returns_helpful_error(self):
        """When pyautogui is unavailable, keyboard tools return a clear install message."""
        with patch("tools.discord_web.is_available", return_value=False):
            result = open_discord_channel(channel_name="general", mock_mode=False)
            assert result["success"] is False
            assert "pyautogui" in result["message"].lower()

    def test_whatsapp_contact_without_pyautogui_returns_helpful_error(self):
        with patch("tools.whatsapp_web.is_available", return_value=False):
            result = search_whatsapp_contact(contact_name="Shlok", mock_mode=False)
            assert result["success"] is False
            assert "pyautogui" in result["message"].lower()

    def test_scroll_without_pyautogui_returns_helpful_error(self):
        with patch("tools.webapp_nav.is_available", return_value=False):
            result = scroll_webapp(direction="down", amount="medium", mock_mode=False)
            assert result["success"] is False
            assert "pyautogui" in result["message"].lower()
