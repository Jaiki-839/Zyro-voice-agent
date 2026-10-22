"""
tests/test_instagram.py -- Tests for tools/instagram.py

All tests use mock_mode=True. No real browser is opened.
Tests cover URL encoding, validation, profile URL, context tracking.
"""
import pytest
from unittest.mock import patch, MagicMock

from core.session import SessionContext
from tools.instagram import (
    open_instagram,
    search_instagram,
    open_instagram_profile,
    open_instagram_reels,
    open_instagram_post,
    refresh_instagram,
    _validate_query,
    _validate_username,
)


class TestInstagramValidation:
    """URL encoding and input validation."""

    def test_validate_query_ok(self):
        ok, val = _validate_query("minecraft")
        assert ok is True
        assert val == "minecraft"

    def test_validate_query_strips_whitespace(self):
        ok, val = _validate_query("  xyz  ")
        assert ok is True
        assert val == "xyz"

    def test_validate_query_empty_fails(self):
        ok, _ = _validate_query("")
        assert ok is False

    def test_validate_query_too_long_fails(self):
        ok, _ = _validate_query("x" * 201)
        assert ok is False

    def test_validate_username_ok(self):
        ok, val = _validate_username("virat.kohli")
        assert ok is True
        assert val == "virat.kohli"

    def test_validate_username_strips_at_sign(self):
        ok, val = _validate_username("@xyz_user")
        assert ok is True
        assert val == "xyz_user"

    def test_validate_username_empty_fails(self):
        ok, _ = _validate_username("")
        assert ok is False

    def test_validate_username_invalid_chars_fail(self):
        ok, _ = _validate_username("user name!")
        assert ok is False

    def test_validate_username_too_long_fails(self):
        ok, _ = _validate_username("x" * 31)
        assert ok is False

    def test_validate_username_allows_hyphens_dots_underscores(self):
        for name in ["user.name", "user_name", "user-name"]:
            ok, val = _validate_username(name)
            assert ok is True, f"Expected {name} to be valid"


class TestInstagramSearch:
    """URL encoding in search_instagram."""

    def test_search_returns_encoded_url(self):
        result = search_instagram(query="hello world", mock_mode=True)
        assert result["success"] is True
        url = result["data"]["url"]
        # space must be encoded
        assert "hello+world" in url or "hello%20world" in url

    def test_search_encodes_special_chars(self):
        result = search_instagram(query="foo&bar=baz", mock_mode=True)
        url = result["data"]["url"]
        assert "&" not in url.split("?q=", 1)[-1]  # raw & must not appear in query param

    def test_search_uses_correct_base_url(self):
        result = search_instagram(query="xyz", mock_mode=True)
        url = result["data"]["url"]
        assert "instagram.com" in url

    def test_search_empty_query_fails(self):
        result = search_instagram(query="", mock_mode=True)
        assert result["success"] is False

    def test_search_updates_session_context(self):
        session = SessionContext()
        search_instagram(query="xyz", mock_mode=True, session=session)
        assert session.webapp.active_app == "instagram"
        assert session.webapp.active_target == "xyz"


class TestInstagramProfile:
    """Profile URL construction."""

    def test_profile_url_correct(self):
        result = open_instagram_profile(username="virat", mock_mode=True)
        assert result["success"] is True
        url = result["data"]["url"]
        assert url == "https://www.instagram.com/virat/"

    def test_profile_from_context(self):
        session = SessionContext()
        session.webapp.update(active_app="instagram", active_target="kohli")
        result = open_instagram_profile(username="", mock_mode=True, session=session)
        assert result["success"] is True
        assert result["data"]["username"] == "kohli"

    def test_profile_no_username_no_context_fails(self):
        result = open_instagram_profile(username="", mock_mode=True)
        assert result["success"] is False

    def test_profile_invalid_username_fails(self):
        result = open_instagram_profile(username="bad user!", mock_mode=True)
        assert result["success"] is False

    def test_profile_updates_page_context(self):
        session = SessionContext()
        open_instagram_profile(username="xyz", mock_mode=True, session=session)
        assert session.webapp.active_page == "profile"
        assert session.webapp.active_target == "xyz"


class TestInstagramReels:
    def test_reels_from_explicit_username(self):
        result = open_instagram_reels(username="user123", mock_mode=True)
        assert result["success"] is True
        assert "/reels/" in result["data"]["url"]

    def test_reels_from_context(self):
        session = SessionContext()
        session.webapp.update(active_app="instagram", active_target="user123")
        result = open_instagram_reels(username="", mock_mode=True, session=session)
        assert result["success"] is True
        assert "user123" in result["data"]["url"]

    def test_reels_no_username_fails(self):
        result = open_instagram_reels(username="", mock_mode=True)
        assert result["success"] is False


class TestInstagramOpen:
    def test_open_sets_active_app(self):
        session = SessionContext()
        result = open_instagram(mock_mode=True, session=session)
        assert result["success"] is True
        assert session.webapp.active_app == "instagram"
        # Previous target/page cleared on switch
        assert session.webapp.active_target is None

    def test_open_returns_context_in_data(self):
        session = SessionContext()
        result = open_instagram(mock_mode=True, session=session)
        assert "context" in result["data"]
        assert result["data"]["context"]["active_app"] == "instagram"


class TestInstagramRefresh:
    def test_refresh_mock(self):
        result = refresh_instagram(mock_mode=True)
        assert result["success"] is True
        assert "[mock]" in result["message"]
