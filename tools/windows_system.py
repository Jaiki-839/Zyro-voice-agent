"""
tools/windows_system.py -- Windows Settings, system utilities, and known folders.

All three tools use hardcoded, validated maps.  No model-generated paths,
URIs, or command strings are ever passed to the OS.  The model picks a key
from an enum; the tool resolves that key to a safe, pre-approved target.

Opening a utility does NOT grant permission to execute arbitrary commands
inside it -- that security boundary remains in core/router.py.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("zyro.windows_system")

# ---------------------------------------------------------------------------
# Hardcoded maps -- the ONLY values that can ever reach the OS
# ---------------------------------------------------------------------------

# ms-settings: URI map.  Opened via start ms-settings:xxx
_SETTINGS_MAP: dict[str, str] = {
    "bluetooth": "ms-settings:bluetooth",
    "network": "ms-settings:network-status",
    "wifi": "ms-settings:network-wifi",
    "ethernet": "ms-settings:network-ethernet",
    "display": "ms-settings:display",
    "sound": "ms-settings:sound",
    "apps": "ms-settings:appsfeatures",
    "installed_apps": "ms-settings:appsfeatures",
    "windows_update": "ms-settings:windowsupdate",
    "update": "ms-settings:windowsupdate",
    "personalization": "ms-settings:personalization",
    "storage": "ms-settings:storagesense",
    "privacy": "ms-settings:privacy",
    "camera": "ms-settings:privacy-webcam",
    "microphone": "ms-settings:privacy-microphone",
    "location": "ms-settings:privacy-location",
    "notifications": "ms-settings:notifications",
    "accounts": "ms-settings:accounts",
    "time": "ms-settings:dateandtime",
    "datetime": "ms-settings:dateandtime",
    "gaming": "ms-settings:gaming-gamebar",
    "accessibility": "ms-settings:easeofaccess",
    "ease_of_access": "ms-settings:easeofaccess",
    "security": "ms-settings:windowsdefender",
    "defender": "ms-settings:windowsdefender",
    "power": "ms-settings:powersleep",
    "battery": "ms-settings:powersleep",
    "multitasking": "ms-settings:multitasking",
    "about": "ms-settings:about",
    "keyboard": "ms-settings:easeofaccess-keyboard",
    "mouse": "ms-settings:easeofaccess-mouse",
    "touchpad": "ms-settings:devices-touchpad",
    "printers": "ms-settings:printers",
    "devices": "ms-settings:connecteddevices",
}

# System utility map.  Values are validated executable names only -- no args.
_UTILITY_MAP: dict[str, list[str]] = {
    "task_manager":   ["taskmgr.exe"],
    "device_manager": ["mmc.exe", "devmgmt.msc"],
    "control_panel":  ["control.exe"],
    "cmd":            ["cmd.exe"],
    "command_prompt": ["cmd.exe"],
    "powershell":     ["powershell.exe"],
    "file_explorer":  ["explorer.exe"],
    "explorer":       ["explorer.exe"],
    "regedit":        ["regedit.exe"],
    "registry_editor": ["regedit.exe"],
}

# Known folder map.  Values are resolved via %USERPROFILE% or shell: paths.
_FOLDER_MAP: dict[str, str] = {
    "downloads":    "downloads",
    "documents":    "documents",
    "desktop":      "desktop",
    "pictures":     "pictures",
    "videos":       "videos",
    "music":        "music",
    "recycle_bin":  "shell:RecycleBinFolder",
    "home":         "home",
    "user":         "home",
}


def _require_windows(name: str) -> dict[str, Any] | None:
    if sys.platform != "win32":
        return {"success": False, "message": f"'{name}' is only available on Windows.", "data": None}
    return None


def _start(target: str) -> None:
    """Open a URI or path via Windows 'start' command."""
    subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)


def _resolve_user_folder(key: str) -> Path | None:
    """Resolve a known folder key to an absolute Path using %USERPROFILE%."""
    profile = os.environ.get("USERPROFILE", "")
    if not profile:
        return None
    base = Path(profile)
    mapping = {
        "downloads": base / "Downloads",
        "documents": base / "Documents",
        "desktop":   base / "Desktop",
        "pictures":  base / "Pictures",
        "videos":    base / "Videos",
        "music":     base / "Music",
        "home":      base,
    }
    return mapping.get(key)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def open_windows_settings(
    category: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Open a Windows Settings page by category name.

    Supported categories: bluetooth, network, wifi, ethernet, display, sound,
    apps, windows_update, personalization, storage, privacy, camera,
    microphone, location, notifications, accounts, time, gaming,
    accessibility, security, power, multitasking, about, keyboard, mouse,
    touchpad, printers, devices.
    """
    err = _require_windows("open_windows_settings")
    if err:
        return err

    key = (category or "").strip().lower().replace(" ", "_").replace("-", "_")
    uri = _SETTINGS_MAP.get(key)
    if uri is None:
        known = sorted(_SETTINGS_MAP.keys())
        return {
            "success": False,
            "message": (
                f"Unknown settings category '{category}'. "
                f"Supported: {', '.join(known[:10])} (and {len(known)-10} more)."
            ),
            "data": {"supported": known},
        }

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would open Windows Settings: {uri}",
            "data": {"uri": uri, "category": key},
        }

    try:
        _start(uri)
        logger.info("Opened Windows Settings: %s -> %s", key, uri)
        return {
            "success": True,
            "message": f"Opening {category} settings.",
            "data": {"uri": uri, "category": key},
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": f"Failed to open {category} settings: {exc}", "data": None}


def open_system_utility(
    utility: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Open a Windows system utility.

    Supported utilities: task_manager, device_manager, control_panel,
    cmd, powershell, file_explorer, regedit.

    Opening a utility does NOT grant permission to run commands inside it.
    """
    err = _require_windows("open_system_utility")
    if err:
        return err

    key = (utility or "").strip().lower().replace(" ", "_").replace("-", "_")
    cmd = _UTILITY_MAP.get(key)
    if cmd is None:
        known = sorted(_UTILITY_MAP.keys())
        return {
            "success": False,
            "message": f"Unknown utility '{utility}'. Supported: {', '.join(known)}.",
            "data": {"supported": known},
        }

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would open utility: {' '.join(cmd)}",
            "data": {"command": cmd, "utility": key},
        }

    try:
        subprocess.Popen(cmd)
        logger.info("Opened utility: %s -> %s", key, cmd)
        display = utility.replace("_", " ").title()
        return {
            "success": True,
            "message": f"Opening {display}.",
            "data": {"command": cmd, "utility": key},
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": f"Failed to open {utility}: {exc}", "data": None}


def open_special_folder(
    folder: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Open a known Windows folder in File Explorer.

    Supported folders: downloads, documents, desktop, pictures, videos,
    music, recycle_bin, home.
    """
    err = _require_windows("open_special_folder")
    if err:
        return err

    key = (folder or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key not in _FOLDER_MAP:
        known = sorted(_FOLDER_MAP.keys())
        return {
            "success": False,
            "message": f"Unknown folder '{folder}'. Supported: {', '.join(known)}.",
            "data": {"supported": known},
        }

    folder_key = _FOLDER_MAP[key]

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would open folder: {folder_key}",
            "data": {"folder": key, "target": folder_key},
        }

    try:
        if folder_key.startswith("shell:"):
            # shell:RecycleBinFolder etc.
            subprocess.Popen(["explorer.exe", folder_key])
        else:
            # resolve via %USERPROFILE%
            path = _resolve_user_folder(folder_key)
            if path is None or not path.exists():
                return {
                    "success": False,
                    "message": f"Could not locate the {folder} folder on this system.",
                    "data": None,
                }
            subprocess.Popen(["explorer.exe", str(path)])

        logger.info("Opened special folder: %s", key)
        display = folder.replace("_", " ").title()
        return {
            "success": True,
            "message": f"Opening {display}.",
            "data": {"folder": key, "target": folder_key},
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": f"Failed to open {folder}: {exc}", "data": None}
