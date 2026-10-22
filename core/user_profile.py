"""
core/user_profile.py — read-only identity/profile for ZYRO and the user.

Sources (in priority order):
  1. Environment variables (always override the JSON file)
  2. data/user_profile.json  (edited manually or by a future settings UI)
  3. Built-in defaults

NEVER invented — if a field is empty everywhere, the caller gets an empty
string and must say "I don't have that information yet."

Env vars recognised:
  ZYRO_NAME                — ZYRO's own name          (default: ZYRO)
  ZYRO_DEVELOPER           — Who made ZYRO             (default: "")
  ZYRO_PURPOSE             — One-line purpose           (default: Windows-first personal AI assistant)
  ZYRO_VERSION             — Version string             (default: 0.1)
  ZYRO_USER_NAME           — User's full/real name      (default: "")
  ZYRO_USER_PREFERRED_NAME — What the user likes to be called (default: "")
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("zyro.user_profile")

# Canonical location relative to the project root (one level up from core/).
_DEFAULT_PROFILE_PATH = Path(__file__).resolve().parent.parent / "data" / "user_profile.json"

# Hard-coded fallbacks when neither env nor file provides a value.
_DEFAULTS: dict[str, dict[str, str]] = {
    "user": {"name": "", "preferred_name": ""},
    "zyro": {
        "name": "ZYRO",
        "developer": "",
        "purpose": "Windows-first personal AI assistant",
        "version": "0.1",
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    """Load the profile JSON file, returning empty dict on any error."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read user_profile.json: %s", exc)
        return {}


class UserProfile:
    """
    Immutable-at-read view of ZYRO's identity and the user's identity.

    Call UserProfile() (or UserProfile(path=...)) to get a loaded profile.
    Every attribute returns a string — empty string means "not configured".
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _DEFAULT_PROFILE_PATH
        file_data = _load_json(self._path)

        user_file = file_data.get("user", {})
        zyro_file = file_data.get("zyro", {})

        # Layer: env > file > default
        self.user_name: str = (
            os.getenv("ZYRO_USER_NAME", "")
            or user_file.get("name", "")
            or _DEFAULTS["user"]["name"]
        ).strip()

        self.user_preferred_name: str = (
            os.getenv("ZYRO_USER_PREFERRED_NAME", "")
            or user_file.get("preferred_name", "")
            or _DEFAULTS["user"]["preferred_name"]
        ).strip()

        self.zyro_name: str = (
            os.getenv("ZYRO_NAME", "")
            or zyro_file.get("name", "")
            or _DEFAULTS["zyro"]["name"]
        ).strip()

        self.developer: str = (
            os.getenv("ZYRO_DEVELOPER", "")
            or zyro_file.get("developer", "")
            or _DEFAULTS["zyro"]["developer"]
        ).strip()

        self.purpose: str = (
            os.getenv("ZYRO_PURPOSE", "")
            or zyro_file.get("purpose", "")
            or _DEFAULTS["zyro"]["purpose"]
        ).strip()

        self.version: str = (
            os.getenv("ZYRO_VERSION", "")
            or zyro_file.get("version", "")
            or _DEFAULTS["zyro"]["version"]
        ).strip()

    # ------------------------------------------------------------------
    # Friendly accessors used by the system instruction builder
    # ------------------------------------------------------------------

    def identity_context(self) -> str:
        """Return a short identity block to inject into the system instruction."""
        lines: list[str] = []

        # ZYRO identity
        lines.append(f"Your name is {self.zyro_name}.")
        lines.append(
            f"Your purpose is: {self.purpose}." if self.purpose else ""
        )
        if self.developer:
            lines.append(f"You were developed by {self.developer}.")
        else:
            lines.append(
                "Your developer information hasn't been configured yet. "
                "Do not invent a developer name."
            )
        lines.append(f"Your version is {self.version}.")

        # User identity
        if self.user_name:
            lines.append(f"The user's name is {self.user_name}.")
        else:
            lines.append(
                "You do not have the user's name saved. "
                "Do not guess it from Windows username, computer name, or file paths."
            )
        if self.user_preferred_name:
            lines.append(f"The user prefers to be called '{self.user_preferred_name}'.")

        return "\n".join(ln for ln in lines if ln)

    def as_dict(self) -> dict[str, Any]:
        return {
            "user": {
                "name": self.user_name,
                "preferred_name": self.user_preferred_name,
            },
            "zyro": {
                "name": self.zyro_name,
                "developer": self.developer,
                "purpose": self.purpose,
                "version": self.version,
            },
        }
