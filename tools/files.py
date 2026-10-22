"""
tools/files.py — search_files, get_file_info, open_file, open_folder,
create_folder, reveal_in_explorer.

File search only ever walks the configured search roots (see config.py /
ZYRO_EXTRA_SEARCH_ROOTS) and only ever returns filename/path/extension/
size/modified-time — never file contents (skills/skill.md #12). Every
path-taking operation validates the path is real and inside an allowed
root before touching it.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from config import CONFIG

_MAX_WALK_ENTRIES = 50_000  # guard against pathological directory trees


def _is_within_allowed_roots(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    for root in CONFIG.search_roots:
        try:
            resolved.relative_to(Path(root).resolve())
            return True
        except ValueError:
            continue
    return False


def _file_entry(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "filename": path.name,
        "path": str(path),
        "extension": path.suffix.lstrip("."),
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def search_files(query: str, extension: str = "", max_results: int = 20, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    query_lower = query.strip().lower()
    if not query_lower:
        return {"success": False, "message": "Please give me something to search for.", "data": None}

    ext_filter = extension.strip().lstrip(".").lower() if extension else None
    matches: list[dict[str, Any]] = []
    scanned = 0

    for root in CONFIG.search_roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
        for dirpath, _dirnames, filenames in os.walk(root_path):
            for fname in filenames:
                scanned += 1
                if scanned > _MAX_WALK_ENTRIES:
                    break
                if ext_filter and not fname.lower().endswith(f".{ext_filter}"):
                    continue
                if query_lower not in fname.lower():
                    continue
                full_path = Path(dirpath) / fname
                try:
                    matches.append(_file_entry(full_path))
                except OSError:
                    continue
                if len(matches) >= max_results:
                    break
            if len(matches) >= max_results:
                break
        if len(matches) >= max_results:
            break

    if not matches:
        return {"success": True, "message": f"No files matching '{query}' were found.", "data": {"results": []}}

    # Most-recently-modified first, so "the latest one" resolves sensibly.
    matches.sort(key=lambda m: m["modified_time"], reverse=True)

    ambiguous_note = ""
    if len(matches) > 1:
        ambiguous_note = " Multiple results were found — ask which one if it's not obvious from context."

    return {
        "success": True,
        "message": f"Found {len(matches)} file(s) matching '{query}'.{ambiguous_note}",
        "data": {"results": matches},
    }


def get_file_info(path: str, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"success": False, "message": f"'{path}' does not exist.", "data": None}
    if not _is_within_allowed_roots(p):
        return {"success": False, "message": f"'{path}' is outside ZYRO's allowed folders.", "data": None}
    return {"success": True, "message": f"Info for {p.name}.", "data": _file_entry(p)}


def open_file(path: str, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"success": False, "message": f"'{path}' does not exist.", "data": None}
    if not p.is_file():
        return {"success": False, "message": f"'{path}' is not a file.", "data": None}
    if not _is_within_allowed_roots(p):
        return {"success": False, "message": f"'{path}' is outside ZYRO's allowed folders.", "data": None}

    if mock_mode:
        return {"success": True, "message": f"[mock] Would open {p.name}.", "data": {"path": str(p)}}

    if sys.platform != "win32":
        return {"success": False, "message": "Opening files is only implemented for Windows.", "data": None}

    try:
        os.startfile(p)  # type: ignore[attr-defined]
    except OSError as exc:
        return {"success": False, "message": f"Could not open '{p.name}': {exc}", "data": None}

    return {"success": True, "message": f"{p.name} opened.", "data": {"path": str(p)}}


def open_folder(path: str, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    p = Path(path)
    if not p.exists() or not p.is_dir():
        return {"success": False, "message": f"'{path}' is not a folder.", "data": None}
    if not _is_within_allowed_roots(p):
        return {"success": False, "message": f"'{path}' is outside ZYRO's allowed folders.", "data": None}

    if mock_mode:
        return {"success": True, "message": f"[mock] Would open folder {p.name}.", "data": {"path": str(p)}}

    if sys.platform != "win32":
        return {"success": False, "message": "Opening folders is only implemented for Windows.", "data": None}

    try:
        os.startfile(p)  # type: ignore[attr-defined]
    except OSError as exc:
        return {"success": False, "message": f"Could not open folder '{p.name}': {exc}", "data": None}

    return {"success": True, "message": f"Folder {p.name} opened.", "data": {"path": str(p)}}


def create_folder(path: str, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    p = Path(path)
    if not _is_within_allowed_roots(p.parent if p.parent != p else p):
        return {"success": False, "message": f"'{path}' is outside ZYRO's allowed folders.", "data": None}
    if p.exists():
        return {"success": False, "message": f"'{path}' already exists.", "data": None}

    if mock_mode:
        return {"success": True, "message": f"[mock] Would create folder {p.name}.", "data": {"path": str(p)}}

    try:
        p.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        return {"success": False, "message": f"Could not create folder '{p.name}': {exc}", "data": None}

    return {"success": True, "message": f"Folder {p.name} created.", "data": {"path": str(p)}}


def reveal_in_explorer(path: str, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"success": False, "message": f"'{path}' does not exist.", "data": None}
    if not _is_within_allowed_roots(p):
        return {"success": False, "message": f"'{path}' is outside ZYRO's allowed folders.", "data": None}

    if mock_mode:
        return {"success": True, "message": f"[mock] Would reveal {p.name} in Explorer.", "data": {"path": str(p)}}

    if sys.platform != "win32":
        return {"success": False, "message": "Explorer integration is only implemented for Windows.", "data": None}

    subprocess.Popen(["explorer", "/select,", str(p)])
    return {"success": True, "message": f"Revealed {p.name} in Explorer.", "data": {"path": str(p)}}
