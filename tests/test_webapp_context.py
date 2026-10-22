"""
tests/test_webapp_context.py -- Tests for core/webapp_context.py

All tests are synchronous and do not touch any real browser or OS.
"""
import pytest
from core.webapp_context import WebAppContext, SUPPORTED_APPS


class TestWebAppContext:
    def test_initial_state_is_empty(self):
        ctx = WebAppContext()
        assert ctx.active_app is None
        assert ctx.active_target is None
        assert ctx.active_page is None
        assert ctx.active_section is None
        assert ctx.last_action is None

    def test_update_sets_known_fields(self):
        ctx = WebAppContext()
        ctx.update(active_app="instagram", active_target="xyz", last_action="search")
        assert ctx.active_app == "instagram"
        assert ctx.active_target == "xyz"
        assert ctx.last_action == "search"

    def test_update_ignores_unknown_fields(self):
        ctx = WebAppContext()
        ctx.update(bogus_field="should_be_ignored")
        assert not hasattr(ctx, "bogus_field")

    def test_switch_app_clears_target_and_page(self):
        ctx = WebAppContext()
        ctx.update(active_app="instagram", active_target="xyz", active_page="profile", active_section="bio")
        ctx.switch_app("discord")
        assert ctx.active_app == "discord"
        assert ctx.active_target is None
        assert ctx.active_page is None
        assert ctx.active_section is None
        assert ctx.last_action == "open_discord"

    def test_clear_resets_all_fields(self):
        ctx = WebAppContext()
        ctx.update(active_app="whatsapp", active_target="Shlok", active_page="chat", last_action="open_contact")
        ctx.clear()
        assert ctx.active_app is None
        assert ctx.active_target is None
        assert ctx.active_page is None
        assert ctx.active_section is None
        assert ctx.last_action is None

    def test_to_dict_returns_all_fields(self):
        ctx = WebAppContext()
        ctx.update(active_app="youtube", active_target="minecraft", last_action="search")
        d = ctx.to_dict()
        assert d["active_app"] == "youtube"
        assert d["active_target"] == "minecraft"
        assert d["last_action"] == "search"
        assert "active_page" in d
        assert "active_section" in d

    def test_is_active_returns_true_for_correct_app(self):
        ctx = WebAppContext()
        ctx.switch_app("spotify")
        assert ctx.is_active("spotify") is True
        assert ctx.is_active("instagram") is False

    def test_supported_apps_set_is_complete(self):
        expected = {"instagram", "discord", "whatsapp", "youtube", "spotify"}
        assert SUPPORTED_APPS == expected

    def test_repr_contains_app_and_target(self):
        ctx = WebAppContext()
        ctx.update(active_app="discord", active_target="General")
        r = repr(ctx)
        assert "discord" in r
        assert "General" in r
