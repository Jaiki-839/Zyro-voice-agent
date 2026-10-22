"""
tools/applications.py — open_application / list_applications.

Applications are resolved through a controlled mapping + safe discovery,
never by executing a model-generated string through a shell (master prompt
section 9 / skills/skill.md #11).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Known aliases -> canonical app key. Extend this as ZYRO learns new apps.
# Keys are lowercase; matching is case-insensitive and substring-tolerant.
_ALIASES: dict[str, str] = {
    "chrome": "chrome", "google chrome": "chrome",
    "discord": "discord",
    "vs code": "vscode", "vscode": "vscode", "visual studio code": "vscode", "code": "vscode",
    "settings": "settings", "windows settings": "settings",
    "notepad": "notepad",
    "explorer": "explorer", "file explorer": "explorer",
    "terminal": "terminal", "cmd": "terminal", "command prompt": "terminal",
    "powershell": "powershell",
    "spotify": "spotify",
    "jaiki cli": "jaiki_cli",
}

# Canonical key -> resolution strategy. `command` is looked up with shutil.which
# first; `winapp` uses the Windows `start shell:AppsFolder\...` / known launch
# verbs; `path_candidates` are checked in order. This mapping is meant to be
# extended per-machine (e.g. via config) rather than guessed at runtime.
_APP_TABLE: dict[str, dict[str, Any]] = {
    "chrome": {"command": "chrome", "windows_start": "chrome"},
    "discord": {"command": "discord", "windows_start": "discord"},
    "vscode": {"command": "code", "windows_start": "code"},
    "notepad": {"command": "notepad", "windows_start": "notepad"},
    "explorer": {"command": "explorer", "windows_start": "explorer"},
    "settings": {"windows_start": "ms-settings:"},
    "terminal": {"windows_start": "wt"},  # Windows Terminal; falls back to cmd
    "powershell": {"command": "powershell", "windows_start": "powershell"},
    "spotify": {"command": "spotify", "windows_start": "spotify"},
    # Project-specific example from the master prompt ("Open Jaiki CLI") —
    # point this at the real executable/script on the target machine.
    "jaiki_cli": {"path_candidates": [], "command": "jaiki-cli"},
}


@dataclass(frozen=True)
class ResolvedApp:
    key: str
    method: str  # "command" | "windows_start" | "path"
    target: str


def resolve_application(name: str) -> ResolvedApp | None:
    """Resolve a spoken app name to something safe to launch, or None."""
    normalized = name.strip().lower()
    key = _ALIASES.get(normalized)
    if key is None:
        # loose contains-match against alias keys, e.g. "open up chrome please"
        for alias, mapped in _ALIASES.items():
            if alias in normalized:
                key = mapped
                break
    if key is None or key not in _APP_TABLE:
        return None

    entry = _APP_TABLE[key]

    for candidate in entry.get("path_candidates", []):
        if Path(candidate).exists():
            return ResolvedApp(key=key, method="path", target=candidate)

    command = entry.get("command")
    if command and shutil.which(command):
        return ResolvedApp(key=key, method="command", target=command)

    windows_start = entry.get("windows_start")
    if windows_start:
        # We don't require it to be resolvable on this (non-Windows) dev
        # machine — `start` resolution happens at launch time on the
        # target Windows system.
        return ResolvedApp(key=key, method="windows_start", target=windows_start)

    return None


def _launch(resolved: ResolvedApp) -> None:
    if sys.platform != "win32":
        raise RuntimeError(f"Application launching is only implemented for Windows (would run: {resolved.target})")

    if resolved.method == "path":
        os.startfile(resolved.target)  # type: ignore[attr-defined]
    elif resolved.method == "command":
        subprocess.Popen([resolved.target])
    elif resolved.method == "windows_start":
        subprocess.Popen(["cmd", "/c", "start", "", resolved.target])
    else:  # pragma: no cover — exhaustive by construction
        raise RuntimeError(f"Unknown resolution method '{resolved.method}'")


def open_application(name: str, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    resolved = resolve_application(name)
    if resolved is None:
        return {"success": False, "message": f"I couldn't find an application called '{name}'.", "data": None}

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would open {name} ({resolved.method}:{resolved.target}).",
            "data": {"application": name, "resolved": resolved.key, "method": resolved.method},
        }

    try:
        _launch(resolved)
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": f"Found '{name}' but failed to launch it: {exc}", "data": None}

    return {
        "success": True,
        "message": f"{name} opened successfully.",
        "data": {"application": name, "resolved": resolved.key, "method": resolved.method},
    }


def list_applications(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    apps = sorted({key for key in _APP_TABLE})
    return {
        "success": True,
        "message": f"ZYRO knows about {len(apps)} applications.",
        "data": {"results": [{"name": a} for a in apps]},
    }
