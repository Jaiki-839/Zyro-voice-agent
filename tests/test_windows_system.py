"""tests/test_windows_system.py -- unit tests for tools/windows_system.py"""
from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from tools.windows_system import (
    _FOLDER_MAP,
    _SETTINGS_MAP,
    _UTILITY_MAP,
    open_special_folder,
    open_system_utility,
    open_windows_settings,
)


def _ok(result):
    assert result["success"] is True, result["message"]


def _fail(result):
    assert result["success"] is False, "Expected failure but got success"


# ---------------------------------------------------------------------------
# Settings map coverage
# ---------------------------------------------------------------------------

class TestSettingsMap:
    def test_all_21_known_settings_categories_exist(self):
        required = [
            "bluetooth", "network", "wifi", "ethernet", "display", "sound",
            "apps", "windows_update", "personalization", "storage", "privacy",
            "camera", "microphone", "location", "notifications", "accounts",
            "time", "gaming", "accessibility", "security", "power",
        ]
        for cat in required:
            assert cat in _SETTINGS_MAP, f"Missing settings category: {cat}"

    def test_all_uris_start_with_ms_settings(self):
        for key, uri in _SETTINGS_MAP.items():
            assert uri.startswith("ms-settings:"), f"{key}: bad URI {uri!r}"


# ---------------------------------------------------------------------------
# open_windows_settings -- mock mode
# ---------------------------------------------------------------------------

class TestOpenWindowsSettingsMock:
    def test_bluetooth(self):
        _ok(open_windows_settings(category="bluetooth", mock_mode=True))

    def test_display(self):
        _ok(open_windows_settings(category="display", mock_mode=True))

    def test_sound(self):
        _ok(open_windows_settings(category="sound", mock_mode=True))

    def test_windows_update(self):
        _ok(open_windows_settings(category="windows_update", mock_mode=True))

    def test_microphone(self):
        _ok(open_windows_settings(category="microphone", mock_mode=True))

    def test_camera(self):
        _ok(open_windows_settings(category="camera", mock_mode=True))

    def test_wifi(self):
        _ok(open_windows_settings(category="wifi", mock_mode=True))

    def test_result_contains_uri(self):
        result = open_windows_settings(category="bluetooth", mock_mode=True)
        assert result["data"]["uri"] == "ms-settings:bluetooth"

    def test_unknown_category_fails(self):
        result = open_windows_settings(category="banana", mock_mode=True)
        _fail(result)
        assert "banana" in result["message"]

    def test_empty_category_fails(self):
        result = open_windows_settings(category="", mock_mode=True)
        _fail(result)

    def test_category_with_spaces_normalized(self):
        """'windows update' should be normalized to 'windows_update'."""
        result = open_windows_settings(category="windows update", mock_mode=True)
        _ok(result)


# ---------------------------------------------------------------------------
# open_system_utility -- mock mode
# ---------------------------------------------------------------------------

class TestOpenSystemUtilityMock:
    def test_task_manager(self):
        _ok(open_system_utility(utility="task_manager", mock_mode=True))

    def test_device_manager(self):
        _ok(open_system_utility(utility="device_manager", mock_mode=True))

    def test_control_panel(self):
        _ok(open_system_utility(utility="control_panel", mock_mode=True))

    def test_cmd(self):
        _ok(open_system_utility(utility="cmd", mock_mode=True))

    def test_powershell(self):
        _ok(open_system_utility(utility="powershell", mock_mode=True))

    def test_file_explorer(self):
        _ok(open_system_utility(utility="file_explorer", mock_mode=True))

    def test_regedit(self):
        _ok(open_system_utility(utility="regedit", mock_mode=True))

    def test_unknown_utility_fails(self):
        result = open_system_utility(utility="blender", mock_mode=True)
        _fail(result)
        assert "blender" in result["message"]

    def test_result_data_has_command(self):
        result = open_system_utility(utility="task_manager", mock_mode=True)
        assert "command" in result["data"]
        assert "taskmgr.exe" in result["data"]["command"]


# ---------------------------------------------------------------------------
# open_special_folder -- mock mode
# ---------------------------------------------------------------------------

class TestOpenSpecialFolderMock:
    def test_downloads(self):
        _ok(open_special_folder(folder="downloads", mock_mode=True))

    def test_documents(self):
        _ok(open_special_folder(folder="documents", mock_mode=True))

    def test_desktop(self):
        _ok(open_special_folder(folder="desktop", mock_mode=True))

    def test_pictures(self):
        _ok(open_special_folder(folder="pictures", mock_mode=True))

    def test_videos(self):
        _ok(open_special_folder(folder="videos", mock_mode=True))

    def test_music(self):
        _ok(open_special_folder(folder="music", mock_mode=True))

    def test_recycle_bin(self):
        result = open_special_folder(folder="recycle_bin", mock_mode=True)
        _ok(result)
        assert "shell:RecycleBinFolder" in result["data"]["target"]

    def test_home(self):
        _ok(open_special_folder(folder="home", mock_mode=True))

    def test_unknown_folder_fails(self):
        result = open_special_folder(folder="system32", mock_mode=True)
        _fail(result)

    def test_empty_folder_fails(self):
        result = open_special_folder(folder="", mock_mode=True)
        _fail(result)


# ---------------------------------------------------------------------------
# Non-Windows graceful degradation
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform == "win32", reason="Testing non-Windows path only")
class TestNonWindows:
    def test_settings_non_windows(self):
        result = open_windows_settings(category="bluetooth", mock_mode=False)
        _fail(result)
        assert "Windows" in result["message"]

    def test_utility_non_windows(self):
        result = open_system_utility(utility="task_manager", mock_mode=False)
        _fail(result)

    def test_folder_non_windows(self):
        result = open_special_folder(folder="downloads", mock_mode=False)
        _fail(result)


# ---------------------------------------------------------------------------
# Windows path (mocked subprocess) -- no actual programs launched
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only tests")
class TestWindowsMocked:
    def test_settings_calls_start(self):
        with patch("tools.windows_system.subprocess.Popen") as mock_popen:
            result = open_windows_settings(category="bluetooth", mock_mode=False)
            _ok(result)
            mock_popen.assert_called_once()
            cmd = mock_popen.call_args.args[0]
            assert "ms-settings:bluetooth" in cmd

    def test_utility_calls_popen(self):
        with patch("tools.windows_system.subprocess.Popen") as mock_popen:
            result = open_system_utility(utility="task_manager", mock_mode=False)
            _ok(result)
            mock_popen.assert_called_once()
            cmd = mock_popen.call_args.args[0]
            assert "taskmgr.exe" in cmd

    def test_folder_downloads(self):
        with (
            patch("tools.windows_system.subprocess.Popen") as mock_popen,
            patch("tools.windows_system._resolve_user_folder") as mock_resolve,
        ):
            from pathlib import Path
            mock_resolve.return_value = Path("C:/Users/Test/Downloads")
            with patch.object(Path, "exists", return_value=True):
                result = open_special_folder(folder="downloads", mock_mode=False)
            _ok(result)
            mock_popen.assert_called_once()


# ---------------------------------------------------------------------------
# Structured result contract
# ---------------------------------------------------------------------------

def test_results_structured():
    for fn, kwargs in [
        (open_windows_settings, {"category": "bluetooth"}),
        (open_system_utility, {"utility": "task_manager"}),
        (open_special_folder, {"folder": "downloads"}),
    ]:
        result = fn(**kwargs, mock_mode=True)
        assert "success" in result
        assert "message" in result
        assert "data" in result
