"""
tools/memory_tools.py — remember_memory, recall_memory, search_memory, forget_memory.

All four handlers follow the ToolDispatcher result convention exactly:
    {"success": bool, "message": str, "data": Any}

The MemoryManager instance is passed in via the `session` argument's
`.memory` attribute, so tools never instantiate their own manager —
the single shared instance lives in core/agent.py (ZyroAgent).

Security rule (inherited from MemoryManager.remember):
  Secrets — passwords, API keys, tokens, private keys — are rejected
  before they reach the JSON file. The handler converts the ValueError
  into a structured failure result.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Tool 1: remember_memory
# ---------------------------------------------------------------------------

def remember_memory(
    key: str,
    value: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Save or update a named memory for the user.

    Only called when the user explicitly asks to remember/save something.
    Rejects secrets (passwords, API keys, tokens).
    Updates the existing memory if the key already exists.
    """
    key = (key or "").strip()
    value = (value or "").strip()

    if not key:
        return {"success": False, "message": "I need a label for what to remember.", "data": None}
    if not value:
        return {"success": False, "message": "I need a value to remember.", "data": None}

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would remember {key} = {value!r}.",
            "data": {"key": key, "value": value},
        }

    manager = _get_manager(session)
    if manager is None:
        return {"success": False, "message": "Memory system is not available right now.", "data": None}

    try:
        entry = manager.remember(key, value)
    except ValueError as exc:
        return {"success": False, "message": str(exc), "data": None}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": f"Could not save the memory: {exc}", "data": None}

    return {
        "success": True,
        "message": f"Saved. I'll remember that {key.replace('_', ' ')} is {value!r}.",
        "data": entry,
    }


# ---------------------------------------------------------------------------
# Tool 2: recall_memory
# ---------------------------------------------------------------------------

def recall_memory(
    key: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Retrieve a specific named memory by its key."""
    key = (key or "").strip()
    if not key:
        return {"success": False, "message": "Please tell me what to look up.", "data": None}

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would recall memory for key '{key}'.",
            "data": {"key": key, "value": "mock-value"},
        }

    manager = _get_manager(session)
    if manager is None:
        return {"success": False, "message": "Memory system is not available right now.", "data": None}

    entry = manager.recall(key)
    if entry is None:
        return {
            "success": False,
            "message": f"I don't have anything saved for '{key.replace('_', ' ')}'.",
            "data": None,
        }

    return {
        "success": True,
        "message": f"I remember that {entry['key'].replace('_', ' ')} is {entry['value']!r}.",
        "data": entry,
    }


# ---------------------------------------------------------------------------
# Tool 3: search_memory
# ---------------------------------------------------------------------------

def search_memory(
    query: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Search all memories for keys or values matching the query string."""
    query = (query or "").strip()
    if not query:
        return {"success": False, "message": "Please give me something to search for.", "data": None}

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would search memories for '{query}'.",
            "data": {"results": [], "query": query},
        }

    manager = _get_manager(session)
    if manager is None:
        return {"success": False, "message": "Memory system is not available right now.", "data": None}

    results = manager.search(query)
    if not results:
        return {
            "success": True,
            "message": f"I don't have any saved memories matching '{query}'.",
            "data": {"results": [], "query": query},
        }

    lines = [f"- {e['key'].replace('_', ' ')}: {e['value']}" for e in results]
    return {
        "success": True,
        "message": "Here's what I found:\n" + "\n".join(lines),
        "data": {"results": results, "query": query},
    }


# ---------------------------------------------------------------------------
# Tool 4: forget_memory
# ---------------------------------------------------------------------------

def forget_memory(
    key: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Remove a saved memory by key."""
    key = (key or "").strip()
    if not key:
        return {"success": False, "message": "Please tell me what to forget.", "data": None}

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would forget memory for key '{key}'.",
            "data": {"key": key},
        }

    manager = _get_manager(session)
    if manager is None:
        return {"success": False, "message": "Memory system is not available right now.", "data": None}

    removed = manager.forget(key)
    if removed:
        return {
            "success": True,
            "message": f"Done. I've forgotten {key.replace('_', ' ')!r}.",
            "data": {"key": key},
        }
    return {
        "success": False,
        "message": f"I don't have anything saved for '{key.replace('_', ' ')}', so nothing was removed.",
        "data": None,
    }


# ---------------------------------------------------------------------------
# Helper: retrieve MemoryManager from session
# ---------------------------------------------------------------------------

def _get_manager(session):
    """Return the MemoryManager attached to the session, or None."""
    if session is None:
        return None
    return getattr(session, "memory", None)
