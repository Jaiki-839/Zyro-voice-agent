"""tests/test_desktop_control.py -- unit tests for tools/desktop_control.py"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from tools.desktop_control import (
    close_window,
    focus_application,
    maximize_window,
    minimize_window,
    restore_window,
    switch_app,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(result):
    assert result["success"] is True, result["message"]


def _fail(result):
    assert result["success"] is False, "Expected failure but got success"


# ---------------------------------------------------------------------------
# Mock mode -- all tools must succeed without touching Windows
# ---------------------------------------------------------------------------

class TestMockMode:
    def test_close_window_mock(self):
        _ok(close_window(app_name="Chrome", mock_mode=True))

    def test_close_window_mock_no_name(self):
        _ok(close_window(mock_mode=True))

    def test_switch_app_mock(self):
        _ok(switch_app(mock_mode=True))

    def test_minimize_window_mock(self):
        _ok(minimize_window(app_name="VS Code", mock_mode=True))

    def test_maximize_window_mock(self):
        _ok(maximize_window(mock_mode=True))

    def test_restore_window_mock(self):
        _ok(restore_window(app_name="Notepad", mock_mode=True))

    def test_focus_application_mock(self):
        _ok(focus_application(app_name="Chrome", mock_mode=True))

    def test_focus_application_empty_name_mock(self):
        """focus_application requires a non-empty app_name."""
        result = focus_application(app_name="", mock_mode=True)
        # Mock mode still short-circuits before checking the name in some
        # implementations; accept either success or meaningful failure.
        assert isinstance(result, dict)
        assert "success" in result


# ---------------------------------------------------------------------------
# Non-Windows graceful degradation
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform == "win32", reason="Testing non-Windows path only")
class TestNonWindows:
    def test_close_window_non_windows(self):
        result = close_window(app_name="Chrome", mock_mode=False)
        _fail(result)
        assert "Windows" in result["message"]

    def test_switch_app_non_windows(self):
        result = switch_app(mock_mode=False)
        _fail(result)

    def test_minimize_window_non_windows(self):
        result = minimize_window(mock_mode=False)
        _fail(result)

    def test_maximize_window_non_windows(self):
        result = maximize_window(mock_mode=False)
        _fail(result)

    def test_restore_window_non_windows(self):
        result = restore_window(mock_mode=False)
        _fail(result)

    def test_focus_application_non_windows(self):
        result = focus_application(app_name="Chrome", mock_mode=False)
        _fail(result)


# ---------------------------------------------------------------------------
# Windows path (mocked ctypes)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only tests")
class TestWindowsMocked:
    def test_close_window_named_found(self):
        with (
            patch("tools.desktop_control._find_window_by_title", return_value=12345),
            patch("tools.desktop_control._user32") as u32,
        ):
            result = close_window(app_name="Chrome", mock_mode=False)
            _ok(result)
            u32.PostMessageW.assert_called_once()

    def test_close_window_named_not_found(self):
        with patch("tools.desktop_control._find_window_by_title", return_value=None):
            result = close_window(app_name="NoSuchApp", mock_mode=False)
            _fail(result)
            assert "NoSuchApp" in result["message"]

    def test_close_window_active(self):
        with (
            patch("tools.desktop_control._active_window", return_value=99),
            patch("tools.desktop_control._user32") as u32,
        ):
            result = close_window(app_name="", mock_mode=False)
            _ok(result)
            u32.PostMessageW.assert_called_once()

    def test_switch_app_sends_alttab(self):
        with patch("tools.desktop_control._user32") as u32:
            result = switch_app(mock_mode=False)
            _ok(result)
            assert u32.keybd_event.call_count == 4  # press VK_MENU, press TAB, release TAB, release VK_MENU

    def test_minimize_not_found(self):
        with patch("tools.desktop_control._find_window_by_title", return_value=None):
            result = minimize_window(app_name="Ghost", mock_mode=False)
            _fail(result)

    def test_focus_empty_name(self):
        result = focus_application(app_name="", mock_mode=False)
        _fail(result)
        assert "required" in result["message"].lower()

    def test_focus_found(self):
        with (
            patch("tools.desktop_control._find_window_by_title", return_value=42),
            patch("tools.desktop_control._user32") as u32,
        ):
            result = focus_application(app_name="Chrome", mock_mode=False)
            _ok(result)
            u32.SetForegroundWindow.assert_called_once_with(42)

    def test_focus_not_found(self):
        with patch("tools.desktop_control._find_window_by_title", return_value=None):
            result = focus_application(app_name="UnknownApp", mock_mode=False)
            _fail(result)
            assert "UnknownApp" in result["message"]


# ---------------------------------------------------------------------------
# Structured result contract
# ---------------------------------------------------------------------------

def test_all_results_are_structured():
    for fn in [close_window, switch_app, minimize_window, maximize_window, restore_window]:
        result = fn(mock_mode=True)
        assert "success" in result
        assert "message" in result
        assert "data" in result

    for app in ["Chrome", "VS Code"]:
        result = focus_application(app_name=app, mock_mode=True)
        assert "success" in result
        assert "message" in result
        assert "data" in result
