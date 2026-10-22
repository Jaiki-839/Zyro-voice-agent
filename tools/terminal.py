"""
tools/terminal.py — open_terminal.

open_terminal() is SAFE and is the only terminal capability shipped in V0.1
(master prompt roadmap). It opens an interactive shell window; it does NOT
run any command on ZYRO's behalf.

run_terminal_command() is intentionally NOT implemented or registered yet.
Per skills/skill.md #13 and #14, if/when it is added it must have: argument
validation, permission checks (CONFIRM at minimum, likely RESTRICTED for
anything touching system state), a timeout, output size limits, and an
explicit confirmation policy — never `execute_anything(command)`. The stub
below exists so the dispatcher/tests have something concrete to reject.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


def open_terminal(cwd: str = "", mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    start_dir = Path(cwd) if cwd else Path.home()
    if not start_dir.exists() or not start_dir.is_dir():
        return {"success": False, "message": f"'{cwd}' is not a valid folder.", "data": None}

    if mock_mode:
        return {"success": True, "message": f"[mock] Would open a terminal in {start_dir}.", "data": {"cwd": str(start_dir)}}

    if sys.platform != "win32":
        return {"success": False, "message": "Terminal launching is only implemented for Windows.", "data": None}

    try:
        subprocess.Popen(["wt", "-d", str(start_dir)])
    except FileNotFoundError:
        # Windows Terminal not installed — fall back to classic cmd.
        subprocess.Popen(["cmd", "/K", f"cd /d {start_dir}"])

    return {"success": True, "message": f"Terminal opened in {start_dir}.", "data": {"cwd": str(start_dir)}}


def run_terminal_command(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    """Not implemented. See module docstring — this must never be wired into
    the tool registry without validation, permission, timeout, output limits,
    and a confirmation policy in place."""
    return {
        "success": False,
        "message": "Running arbitrary terminal commands is not enabled in this version of ZYRO.",
        "data": None,
    }
