"""
tools/windows.py — small Windows-specific helpers shared by other tool
modules (not a tool itself / not registered directly).

Dangerous Windows operations (shutdown/restart, registry changes, disk
formatting, security settings) are deliberately NOT implemented anywhere
in ZYRO yet. Per skills/skill.md #14 they would need to be RESTRICTED at
minimum, with explicit confirmation, if ever added.
"""
from __future__ import annotations

import platform
import sys


def is_windows() -> bool:
    return sys.platform == "win32"


def windows_version() -> str:
    if not is_windows():
        return "not running on Windows"
    return platform.platform()
