"""tests/test_media_control.py -- unit tests for tools/media_control.py"""
from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from tools.media_control import (
    VK_MEDIA_NEXT_TRACK,
    VK_MEDIA_PLAY_PAUSE,
    VK_MEDIA_PREV_TRACK,
    VK_VOLUME_DOWN,
    VK_VOLUME_MUTE,
    VK_VOLUME_UP,
    media_mute,
    media_next,
    media_pause,
    media_play,
    media_play_pause,
    media_previous,
    media_unmute,
    media_volume_down,
    media_volume_up,
)

_ALL_TOOLS = [
    media_play,
    media_pause,
    media_play_pause,
    media_next,
    media_previous,
    media_volume_up,
    media_volume_down,
    media_mute,
    media_unmute,
]


def _ok(result):
    assert result["success"] is True, result["message"]


def _fail(result):
    assert result["success"] is False


# ---------------------------------------------------------------------------
# Mock mode -- all 9 tools must succeed
# ---------------------------------------------------------------------------

class TestMockMode:
    def test_media_play_mock(self):
        _ok(media_play(mock_mode=True))

    def test_media_pause_mock(self):
        _ok(media_pause(mock_mode=True))

    def test_media_play_pause_mock(self):
        _ok(media_play_pause(mock_mode=True))

    def test_media_next_mock(self):
        _ok(media_next(mock_mode=True))

    def test_media_previous_mock(self):
        _ok(media_previous(mock_mode=True))

    def test_media_volume_up_mock(self):
        _ok(media_volume_up(mock_mode=True))

    def test_media_volume_down_mock(self):
        _ok(media_volume_down(mock_mode=True))

    def test_media_mute_mock(self):
        _ok(media_mute(mock_mode=True))

    def test_media_unmute_mock(self):
        _ok(media_unmute(mock_mode=True))


# ---------------------------------------------------------------------------
# Non-Windows graceful degradation
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform == "win32", reason="Testing non-Windows path only")
class TestNonWindows:
    def test_all_tools_fail_gracefully_non_windows(self):
        for fn in _ALL_TOOLS:
            result = fn(mock_mode=False)
            _fail(result)
            assert "Windows" in result["message"]


# ---------------------------------------------------------------------------
# Virtual key code constants
# ---------------------------------------------------------------------------

class TestVKConstants:
    def test_play_pause_vk(self):
        assert VK_MEDIA_PLAY_PAUSE == 0xB3

    def test_next_track_vk(self):
        assert VK_MEDIA_NEXT_TRACK == 0xB0

    def test_prev_track_vk(self):
        assert VK_MEDIA_PREV_TRACK == 0xB1

    def test_volume_up_vk(self):
        assert VK_VOLUME_UP == 0xAF

    def test_volume_down_vk(self):
        assert VK_VOLUME_DOWN == 0xAE

    def test_mute_vk(self):
        assert VK_VOLUME_MUTE == 0xAD


# ---------------------------------------------------------------------------
# Windows path (mocked ctypes) -- verify correct VK code dispatched
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only tests")
class TestWindowsMocked:
    def _pressed_vk(self, mock_u32):
        """Return list of VK codes that were pressed (non-keyup calls)."""
        return [
            call.args[0]
            for call in mock_u32.keybd_event.call_args_list
            if len(call.args) >= 3 and call.args[2] == 0  # KEYDOWN flag == 0
        ]

    def test_media_play_uses_play_pause_vk(self):
        with patch("tools.media_control._user32") as u32:
            _ok(media_play(mock_mode=False))
            assert VK_MEDIA_PLAY_PAUSE in self._pressed_vk(u32)

    def test_media_next_uses_next_track_vk(self):
        with patch("tools.media_control._user32") as u32:
            _ok(media_next(mock_mode=False))
            assert VK_MEDIA_NEXT_TRACK in self._pressed_vk(u32)

    def test_media_previous_uses_prev_track_vk(self):
        with patch("tools.media_control._user32") as u32:
            _ok(media_previous(mock_mode=False))
            assert VK_MEDIA_PREV_TRACK in self._pressed_vk(u32)

    def test_media_volume_up_uses_vk(self):
        with patch("tools.media_control._user32") as u32:
            _ok(media_volume_up(mock_mode=False))
            assert VK_VOLUME_UP in self._pressed_vk(u32)

    def test_media_mute_uses_mute_vk(self):
        with patch("tools.media_control._user32") as u32:
            _ok(media_mute(mock_mode=False))
            assert VK_VOLUME_MUTE in self._pressed_vk(u32)

    def test_media_unmute_uses_mute_vk(self):
        """Unmute is the same physical key as mute (Windows toggle)."""
        with patch("tools.media_control._user32") as u32:
            _ok(media_unmute(mock_mode=False))
            assert VK_VOLUME_MUTE in self._pressed_vk(u32)


# ---------------------------------------------------------------------------
# Structured result contract
# ---------------------------------------------------------------------------

def test_all_results_structured():
    for fn in _ALL_TOOLS:
        result = fn(mock_mode=True)
        assert "success" in result
        assert "message" in result
        assert "data" in result


# ---------------------------------------------------------------------------
# Play does NOT open YouTube
# ---------------------------------------------------------------------------

def test_media_play_message_does_not_mention_youtube():
    result = media_play(mock_mode=True)
    assert "youtube" not in result["message"].lower()
    assert "open" not in result["message"].lower() or "mock" in result["message"].lower()
