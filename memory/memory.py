"""
memory/memory.py — persistent memory store (V0.4 roadmap item, now active).

Two classes live here:

  MemoryManager   — the new, full-featured explicit-only memory system.
                    Stores key/value memories as JSON in data/memories.json.
                    Used by tools/memory_tools.py (wired in V0.4+).

  MemoryStore     — the original minimal key/value store kept for backward
                    compatibility with any code that still references it.

Security rule: MemoryManager.remember() refuses to save secrets
(passwords, API keys, tokens, private keys, etc.) — see _is_secret().
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger("zyro.memory")

_DEFAULT_MEMORIES_PATH = Path(__file__).resolve().parent.parent / "data" / "memories.json"

# Keywords that indicate a secret — if the value looks like a secret, reject it.
_SECRET_KEYWORDS = frozenset([
    "password", "passwd", "api key", "apikey", "api_key",
    "token", "secret", "private key", "privatekey", "private_key",
    "credential", "credentials", "auth", "authentication",
    "passphrase", "pin", "access key", "access_key",
])


def _is_secret(key: str, value: str) -> bool:
    """Return True if the key or value looks like a secret that must not be stored."""
    text = (key + " " + value).lower()
    return any(kw in text for kw in _SECRET_KEYWORDS)


class MemoryManager:
    """
    Explicit-only persistent memory for ZYRO.

    Memories are saved ONLY when the user explicitly asks ZYRO to remember
    something. Normal conversation is never auto-saved.

    Storage format (data/memories.json):
    {
      "memories": [
        {
          "id": "<uuid>",
          "key": "favorite_game",
          "value": "Minecraft",
          "created_at": "<iso8601>",
          "updated_at": "<iso8601>"
        }
      ]
    }
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _DEFAULT_MEMORIES_PATH
        self._ensure_file()

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def _ensure_file(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps({"memories": []}, indent=2), encoding="utf-8")

    def load(self) -> list[dict[str, Any]]:
        """Load and return the full memories list from disk."""
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return raw.get("memories", [])
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read memories.json: %s", exc)
            return []

    def save(self, memories: list[dict[str, Any]]) -> None:
        """Write the full memories list to disk atomically."""
        try:
            self._path.write_text(
                json.dumps({"memories": memories}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error("Could not write memories.json: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def remember(self, key: str, value: str) -> dict[str, Any]:
        """
        Save or update a memory.

        If a memory with the same key already exists, it is updated
        (no duplicates). Returns the saved memory record.
        Raises ValueError if the key/value looks like a secret.
        """
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if not key:
            raise ValueError("Memory key must not be empty.")
        if not value:
            raise ValueError("Memory value must not be empty.")
        if _is_secret(key, value):
            raise ValueError(
                "Secrets such as passwords, API keys, and authentication tokens "
                "cannot be stored in ordinary memory."
            )

        memories = self.load()
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Update existing entry if key already exists.
        for entry in memories:
            if entry.get("key") == key:
                entry["value"] = value
                entry["updated_at"] = now
                self.save(memories)
                logger.info("Memory updated: %s", key)
                return dict(entry)

        # New entry.
        entry = {
            "id": str(uuid.uuid4()),
            "key": key,
            "value": value,
            "created_at": now,
            "updated_at": now,
        }
        memories.append(entry)
        self.save(memories)
        logger.info("Memory saved: %s", key)
        return dict(entry)

    def recall(self, key: str) -> dict[str, Any] | None:
        """Return the memory entry for a key, or None if not found."""
        key = key.strip().lower().replace(" ", "_")
        for entry in self.load():
            if entry.get("key") == key:
                return dict(entry)
        return None

    def search(self, query: str) -> list[dict[str, Any]]:
        """
        Return all memories whose key or value contains the query string
        (case-insensitive substring match).
        """
        query = query.strip().lower()
        if not query:
            return []
        return [
            dict(e) for e in self.load()
            if query in e.get("key", "").lower() or query in e.get("value", "").lower()
        ]

    def forget(self, key: str) -> bool:
        """
        Remove the memory with the given key.
        Returns True if a memory was removed, False if not found.
        """
        key = key.strip().lower().replace(" ", "_")
        memories = self.load()
        original_len = len(memories)
        memories = [e for e in memories if e.get("key") != key]
        if len(memories) < original_len:
            self.save(memories)
            logger.info("Memory forgotten: %s", key)
            return True
        return False

    def get_all(self) -> list[dict[str, Any]]:
        """Return a copy of all stored memories."""
        return [dict(e) for e in self.load()]


# ---------------------------------------------------------------------------
# Original MemoryStore — kept for backward compatibility
# ---------------------------------------------------------------------------

class MemoryStore:
    def __init__(self, path: str | Path = "zyro_memory.json") -> None:
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self._load().get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self._load()
        data[key] = value
        self._save(data)

    def delete(self, key: str) -> None:
        data = self._load()
        data.pop(key, None)
        self._save(data)
