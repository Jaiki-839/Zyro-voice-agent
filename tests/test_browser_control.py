"""tests/test_browser_control.py -- unit tests for tools/browser_control.py"""
from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from tools.browser_control import (
    close_browser_tab,
    next_browser_tab,
    open_new_browser_tab,
    previous_browser_tab,
    switch_to_browser_tab,
)


def _ok(result):
    assert result["success"] is True, result["message"]

def _fail(result):
    assert result["success"] is False, "Expected failure but got success"


# ---------------------------------------------------------------------------
# Mock mode
# ---------------------------------------------------------------------------

class TestMockMode:
    def test_next_tab_mock(self):
        _ok(next_browser_tab(mock_mode=True))

    def test_previous_tab_mock(self):
        _ok(previous_browser_tab(mock_mode=True))

    def test_close_tab_mock(self):
        _ok(close_browser_tab(mock_mode=True))

    def test_new_tab_mock(self):
        _ok(open_new_browser_tab(mock_mode=True))

    def test_switch_to_tab_1_mock(self):
        _ok(switch_to_browser_tab(tab_number=1, mock_mode=True))

    def test_switch_to_tab_9_mock(self):
        result = switch_to_browser_tab(tab_number=9, mock_mode=True)
        _ok(result)

    def test_switch_to_tab_5_mock(self):
        _ok(switch_to_browser_tab(tab_number=5, mock_mode=True))


# ---------------------------------------------------------------------------
# tab_number validation
# ---------------------------------------------------------------------------

class TestTabNumberValidation:
    def test_tab_0_rejected(self):
        result = switch_to_browser_tab(tab_number=0, mock_mode=True)
        _fail(result)
        assert "1" in result["message"] and "9" in result["message"]

    def test_tab_10_rejected(self):
        result = switch_to_browser_tab(tab_number=10, mock_mode=True)
        _fail(result)

    def test_tab_negative_rejected(self):
        result = switch_to_browser_tab(tab_number=-1, mock_mode=True)
        _fail(result)

    def test_tab_string_rejected(self):
        result = switch_to_browser_tab(tab_number="three", mock_mode=True)  # type: ignore
        _fail(result)


# ---------------------------------------------------------------------------
# Non-Windows graceful degradation
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform == "win32", reason="Testing non-Windows path only")
class TestNonWindows:
    def test_next_tab_non_windows(self):
        _fail(next_browser_tab(mock_mode=False))

    def test_previous_tab_non_windows(self):
        _fail(previous_browser_tab(mock_mode=False))

    def test_close_tab_non_windows(self):
        _fail(close_browser_tab(mock_mode=False))

    def test_new_tab_non_windows(self):
        _fail(open_new_browser_tab(mock_mode=False))

    def test_switch_tab_non_windows(self):
        _fail(switch_to_browser_tab(tab_number=3, mock_mode=False))


# ---------------------------------------------------------------------------
# Windows path (mocked ctypes)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only tests")
class TestWindowsMocked:
    def test_next_tab_sends_ctrl_tab(self):
        with patch("tools.browser_control._user32") as u32:
            result = next_browser_tab(mock_mode=False)
            _ok(result)
            assert u32.keybd_event.call_count >= 2

    def test_switch_to_tab_3(self):
        with patch("tools.browser_control._user32") as u32:
            result = switch_to_browser_tab(tab_number=3, mock_mode=False)
            _ok(result)
            # Should press Ctrl + digit-3 (VK = 0x33)
            calls = [call.args[0] for call in u32.keybd_event.call_args_list]
            assert 0x11 in calls  # VK_CONTROL
            assert 0x33 in calls  # '3'

    def test_switch_to_tab_9_uses_ctrl9(self):
        with patch("tools.browser_control._user32") as u32:
            result = switch_to_browser_tab(tab_number=9, mock_mode=False)
            _ok(result)
            calls = [call.args[0] for call in u32.keybd_event.call_args_list]
            assert 0x39 in calls  # '9' VK


# ---------------------------------------------------------------------------
# Structured result contract
# ---------------------------------------------------------------------------

def test_all_results_structured():
    for fn in [next_browser_tab, previous_browser_tab, close_browser_tab, open_new_browser_tab]:
        result = fn(mock_mode=True)
        assert "success" in result
        assert "message" in result
        assert "data" in result

    result = switch_to_browser_tab(tab_number=2, mock_mode=True)
    assert "success" in result
    assert "message" in result
    assert "data" in result
