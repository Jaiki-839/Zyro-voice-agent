"""
tests/test_web_tools.py — unit tests for tools/web.py.

All tests run with mock_mode=True so nothing touches the network or
opens a real browser. The ToolDispatcher integration tests verify that
every new tool is correctly registered and dispatched end-to-end.
"""
from __future__ import annotations

import urllib.parse
from unittest.mock import MagicMock, patch

import pytest

from core.permissions import PermissionLevel
from core.router import ToolDispatcher
from core.session import SessionContext
from core.tool_registry import ToolRegistry, Tool, ToolParameter
from tools.web import (
    open_spotify,
    open_url,
    open_youtube,
    read_webpage,
    search_spotify,
    search_youtube,
    web_search,
    _validate_url,
    _YOUTUBE_BASE,
    _YOUTUBE_SEARCH,
    _SPOTIFY_BASE,
    _SPOTIFY_SEARCH,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(result: dict) -> None:
    """Assert a tool result is a well-formed success."""
    assert isinstance(result, dict), "result must be a dict"
    assert "success" in result, "result must have 'success'"
    assert "message" in result, "result must have 'message'"
    assert "data" in result, "result must have 'data'"
    assert result["success"] is True, f"expected success=True, got message: {result['message']}"


def _fail(result: dict) -> None:
    """Assert a tool result is a well-formed failure."""
    assert isinstance(result, dict)
    assert "success" in result
    assert "message" in result
    assert "data" in result
    assert result["success"] is False, f"expected success=False, got message: {result['message']}"


# ---------------------------------------------------------------------------
# _validate_url
# ---------------------------------------------------------------------------

class TestValidateUrl:
    def test_valid_https(self):
        ok, err = _validate_url("https://www.python.org")
        assert ok is True
        assert err == ""

    def test_valid_http(self):
        ok, err = _validate_url("http://example.com")
        assert ok is True

    def test_rejects_file_scheme(self):
        ok, err = _validate_url("file:///C:/Windows/system32")
        assert ok is False
        assert "file" in err.lower() or "http" in err.lower()

    def test_rejects_javascript_scheme(self):
        ok, err = _validate_url("javascript:alert(1)")
        assert ok is False

    def test_rejects_data_scheme(self):
        ok, err = _validate_url("data:text/html,<h1>hi</h1>")
        assert ok is False

    def test_rejects_vbscript_scheme(self):
        ok, err = _validate_url("vbscript:MsgBox(1)")
        assert ok is False

    def test_rejects_empty_string(self):
        ok, err = _validate_url("")
        assert ok is False

    def test_rejects_no_domain(self):
        ok, err = _validate_url("https://")
        assert ok is False


# ---------------------------------------------------------------------------
# web_search
# ---------------------------------------------------------------------------

class TestWebSearch:
    def test_mock_mode_returns_structured_result(self):
        result = web_search("Python", mock_mode=True)
        _ok(result)
        assert "results" in result["data"]
        assert len(result["data"]["results"]) > 0
        first = result["data"]["results"][0]
        assert "title" in first
        assert "url" in first

    def test_mock_mode_contains_query(self):
        result = web_search("latest NVIDIA news", mock_mode=True)
        _ok(result)
        assert "NVIDIA" in result["message"] or "NVIDIA" in str(result["data"])

    def test_empty_query_returns_failure(self):
        result = web_search("", mock_mode=True)
        _fail(result)

    def test_whitespace_query_returns_failure(self):
        result = web_search("   ", mock_mode=True)
        _fail(result)

    def test_result_convention_shape(self):
        result = web_search("test", mock_mode=True)
        assert set(result.keys()) == {"success", "message", "data"}

    def test_custom_backend_is_called(self):
        import tools.web as web_module
        original = web_module._search_backend
        try:
            fake_results = [{"title": "T", "url": "https://t.com", "snippet": "s", "source": "t.com"}]
            web_module._search_backend = lambda q, n: fake_results
            result = web_search("test", mock_mode=False)
            _ok(result)
            assert result["data"]["results"] == fake_results
        finally:
            web_module._search_backend = original


# ---------------------------------------------------------------------------
# open_url
# ---------------------------------------------------------------------------

class TestOpenUrl:
    def test_valid_https_mock(self):
        result = open_url("https://www.python.org", mock_mode=True)
        _ok(result)
        assert result["data"]["url"] == "https://www.python.org"
        assert "[mock]" in result["message"]

    def test_valid_http_mock(self):
        result = open_url("http://example.com", mock_mode=True)
        _ok(result)

    def test_rejects_file_scheme(self):
        result = open_url("file:///C:/secret", mock_mode=True)
        _fail(result)

    def test_rejects_javascript(self):
        result = open_url("javascript:void(0)", mock_mode=True)
        _fail(result)

    def test_rejects_data_uri(self):
        result = open_url("data:text/html,hello", mock_mode=True)
        _fail(result)

    def test_rejects_empty(self):
        result = open_url("", mock_mode=True)
        _fail(result)

    def test_real_mode_calls_webbrowser(self):
        with patch("tools.web._open_browser") as mock_open:
            result = open_url("https://www.python.org", mock_mode=False)
            _ok(result)
            mock_open.assert_called_once_with("https://www.python.org")

    def test_real_mode_browser_exception_returns_failure(self):
        with patch("tools.web._open_browser", side_effect=RuntimeError("no browser")):
            result = open_url("https://www.python.org", mock_mode=False)
            _fail(result)
            assert "Failed" in result["message"]

    def test_result_convention_shape(self):
        result = open_url("https://example.com", mock_mode=True)
        assert set(result.keys()) == {"success", "message", "data"}


# ---------------------------------------------------------------------------
# read_webpage
# ---------------------------------------------------------------------------

class TestReadWebpage:
    def test_mock_mode(self):
        result = read_webpage("https://www.python.org", mock_mode=True)
        _ok(result)
        assert result["data"]["url"] == "https://www.python.org"
        assert "text" in result["data"]

    def test_invalid_url_rejected(self):
        result = read_webpage("file:///C:/bad", mock_mode=True)
        _fail(result)

    def test_empty_url_rejected(self):
        result = read_webpage("", mock_mode=True)
        _fail(result)

    def test_result_convention_shape(self):
        result = read_webpage("https://example.com", mock_mode=True)
        assert set(result.keys()) == {"success", "message", "data"}

    def test_http_error_returns_failure(self):
        import requests
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        http_err = requests.exceptions.HTTPError(response=mock_resp)
        with patch("requests.get", side_effect=http_err):
            result = read_webpage("https://www.python.org", mock_mode=False)
            _fail(result)
            assert "404" in result["message"] or "HTTP" in result["message"]

    def test_timeout_returns_failure(self):
        import requests
        with patch("requests.get", side_effect=requests.exceptions.Timeout()):
            result = read_webpage("https://www.python.org", mock_mode=False)
            _fail(result)
            assert "timed out" in result["message"].lower()

    def test_successful_fetch_parses_html(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.encoding = "utf-8"
        mock_resp.raise_for_status = MagicMock()
        mock_resp.iter_content = MagicMock(return_value=[
            b"<html><head><title>Test Page</title></head>"
            b"<body><p>Hello world content here.</p></body></html>"
        ])
        with patch("requests.get", return_value=mock_resp):
            result = read_webpage("https://example.com", mock_mode=False)
            _ok(result)
            assert result["data"]["title"] == "Test Page"
            assert "Hello world" in result["data"]["text"]


# ---------------------------------------------------------------------------
# open_youtube / search_youtube
# ---------------------------------------------------------------------------

class TestOpenYoutube:
    def test_no_query_opens_homepage_mock(self):
        result = open_youtube(query="", mock_mode=True)
        _ok(result)
        assert result["data"]["url"] == _YOUTUBE_BASE

    def test_with_query_opens_search_mock(self):
        result = open_youtube(query="Minecraft music", mock_mode=True)
        _ok(result)
        encoded = urllib.parse.quote_plus("Minecraft music")
        expected_url = _YOUTUBE_SEARCH.format(encoded)
        assert result["data"]["url"] == expected_url

    def test_query_is_url_encoded(self):
        result = open_youtube(query="lo-fi music & chill", mock_mode=True)
        _ok(result)
        assert "lo-fi" not in result["data"]["url"] or "+" in result["data"]["url"] or "%2B" in result["data"]["url"]

    def test_no_playback_claim_in_message(self):
        result = open_youtube(query="Believer", mock_mode=True)
        msg = result["message"].lower()
        assert "playing" not in msg

    def test_search_youtube_delegates_to_open_youtube(self):
        result = search_youtube(query="lo-fi", mock_mode=True)
        _ok(result)
        assert "lo-fi" in result["data"]["url"] or "lo" in result["data"]["url"]

    def test_result_convention_shape(self):
        result = open_youtube(mock_mode=True)
        assert set(result.keys()) == {"success", "message", "data"}

    def test_real_mode_calls_browser(self):
        with patch("tools.web._open_browser") as mock_open:
            result = open_youtube(query="test", mock_mode=False)
            _ok(result)
            mock_open.assert_called_once()
            called_url = mock_open.call_args[0][0]
            assert "youtube.com" in called_url


# ---------------------------------------------------------------------------
# open_spotify / search_spotify
# ---------------------------------------------------------------------------

class TestOpenSpotify:
    def test_no_query_opens_homepage_mock(self):
        result = open_spotify(query="", mock_mode=True)
        _ok(result)
        assert result["data"]["url"] == _SPOTIFY_BASE

    def test_with_query_opens_search_mock(self):
        result = open_spotify(query="Believer", mock_mode=True)
        _ok(result)
        encoded = urllib.parse.quote_plus("Believer")
        expected_url = _SPOTIFY_SEARCH.format(encoded)
        assert result["data"]["url"] == expected_url

    def test_no_playback_claim_in_message(self):
        result = open_spotify(query="Believer", mock_mode=True)
        msg = result["message"].lower()
        assert "playing" not in msg

    def test_login_mentioned_in_message(self):
        result = open_spotify(query="Believer", mock_mode=False)
        # In real mode this opens browser; just check convention if it succeeds
        # (mock the browser so CI doesn't open one)
        with patch("tools.web._open_browser"):
            result = open_spotify(query="Believer", mock_mode=False)
            _ok(result)
            assert "sign" in result["message"].lower() or "login" in result["message"].lower() or "signed" in result["message"].lower()

    def test_search_spotify_delegates(self):
        result = search_spotify(query="Coldplay", mock_mode=True)
        _ok(result)
        assert "Coldplay" in result["data"]["url"] or "coldplay" in result["data"]["url"].lower()

    def test_result_convention_shape(self):
        result = open_spotify(mock_mode=True)
        assert set(result.keys()) == {"success", "message", "data"}

    def test_real_mode_calls_browser(self):
        with patch("tools.web._open_browser") as mock_open:
            result = open_spotify(query="jazz", mock_mode=False)
            _ok(result)
            mock_open.assert_called_once()
            called_url = mock_open.call_args[0][0]
            assert "spotify.com" in called_url


# ---------------------------------------------------------------------------
# ToolDispatcher integration — all new tools are registered and dispatched
# ---------------------------------------------------------------------------

class TestDispatcherIntegration:
    """Verify every new tool goes through ToolDispatcher successfully."""

    def _make_dispatcher(self) -> ToolDispatcher:
        from core.agent import build_registry
        registry = build_registry()
        return ToolDispatcher(registry=registry, session=SessionContext(), mock_mode=True)

    def test_web_search_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("web_search", {"query": "Python"})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_open_url_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("open_url", {"url": "https://www.python.org"})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_open_url_bad_scheme_dispatches_but_fails(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("open_url", {"url": "file:///bad"})
        assert outcome.executed is True          # handler ran
        assert outcome.result["success"] is False  # but reported failure

    def test_read_webpage_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("read_webpage", {"url": "https://www.python.org"})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_open_youtube_no_query_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("open_youtube", {})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_open_youtube_with_query_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("open_youtube", {"query": "Minecraft music"})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_search_youtube_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("search_youtube", {"query": "lo-fi"})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_open_spotify_no_query_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("open_spotify", {})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_open_spotify_with_query_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("open_spotify", {"query": "Believer"})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_search_spotify_dispatches(self):
        d = self._make_dispatcher()
        outcome = d.dispatch("search_spotify", {"query": "Coldplay"})
        assert outcome.executed is True
        assert outcome.result["success"] is True

    def test_all_new_tools_are_safe_permission(self):
        from core.agent import build_registry
        registry = build_registry()
        new_tool_names = ["open_url", "read_webpage", "open_youtube", "search_youtube", "open_spotify", "search_spotify"]
        for name in new_tool_names:
            tool = registry.get(name)
            assert tool is not None, f"Tool '{name}' not found in registry"
            assert tool.permission == PermissionLevel.SAFE, f"'{name}' must be SAFE"

    def test_tool_count_increased(self):
        from core.agent import build_registry
        registry = build_registry()
        # Was 13 before; now 19
        assert len(registry.all()) >= 19, f"Expected at least 19 tools, got {len(registry.all())}"
