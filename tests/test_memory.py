"""
tests/test_memory.py — unit tests for memory/memory.py (MemoryManager).

All tests use a temporary file so they never touch data/memories.json.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from memory.memory import MemoryManager, _is_secret


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_manager(tmp_path):
    """MemoryManager backed by a temp file — isolated per test."""
    return MemoryManager(path=tmp_path / "memories.json")


# ---------------------------------------------------------------------------
# _is_secret
# ---------------------------------------------------------------------------

class TestIsSecret:
    def test_password_key_detected(self):
        assert _is_secret("password", "hunter2") is True

    def test_api_key_in_key(self):
        assert _is_secret("api_key", "sk-abc123") is True

    def test_token_in_key(self):
        assert _is_secret("auth_token", "eyJhbGciO...") is True

    def test_safe_value_not_secret(self):
        assert _is_secret("favorite_game", "Minecraft") is False

    def test_safe_programming_language(self):
        assert _is_secret("preferred_language", "Python") is False

    def test_secret_keyword_in_value(self):
        assert _is_secret("my_stuff", "my password is 1234") is True


# ---------------------------------------------------------------------------
# MemoryManager.remember
# ---------------------------------------------------------------------------

class TestRemember:
    def test_saves_new_memory(self, tmp_manager):
        entry = tmp_manager.remember("favorite_game", "Minecraft")
        assert entry["key"] == "favorite_game"
        assert entry["value"] == "Minecraft"
        assert "id" in entry
        assert "created_at" in entry
        assert "updated_at" in entry

    def test_updates_existing_key(self, tmp_manager):
        tmp_manager.remember("favorite_game", "Minecraft")
        entry = tmp_manager.remember("favorite_game", "Valorant")
        assert entry["value"] == "Valorant"
        # Must not create a duplicate
        all_mem = tmp_manager.get_all()
        game_entries = [e for e in all_mem if e["key"] == "favorite_game"]
        assert len(game_entries) == 1

    def test_rejects_empty_key(self, tmp_manager):
        with pytest.raises(ValueError, match="key"):
            tmp_manager.remember("", "value")

    def test_rejects_empty_value(self, tmp_manager):
        with pytest.raises(ValueError, match="value"):
            tmp_manager.remember("key", "")

    def test_rejects_secret_key(self, tmp_manager):
        with pytest.raises(ValueError, match="[Ss]ecret"):
            tmp_manager.remember("password", "hunter2")

    def test_rejects_token_key(self, tmp_manager):
        with pytest.raises(ValueError, match="[Ss]ecret"):
            tmp_manager.remember("api_key", "sk-abc")

    def test_key_normalised_to_lowercase(self, tmp_manager):
        entry = tmp_manager.remember("Favorite Game", "Minecraft")
        assert entry["key"] == "favorite_game"

    def test_persists_across_instances(self, tmp_path):
        path = tmp_path / "m.json"
        m1 = MemoryManager(path=path)
        m1.remember("lang", "Python")
        m2 = MemoryManager(path=path)
        entry = m2.recall("lang")
        assert entry is not None
        assert entry["value"] == "Python"


# ---------------------------------------------------------------------------
# MemoryManager.recall
# ---------------------------------------------------------------------------

class TestRecall:
    def test_recalls_saved_memory(self, tmp_manager):
        tmp_manager.remember("favorite_game", "Minecraft")
        entry = tmp_manager.recall("favorite_game")
        assert entry is not None
        assert entry["value"] == "Minecraft"

    def test_returns_none_for_missing_key(self, tmp_manager):
        assert tmp_manager.recall("nonexistent") is None

    def test_case_insensitive_key_lookup(self, tmp_manager):
        tmp_manager.remember("favorite_game", "Minecraft")
        # Keys are normalised on save; lookup should also normalise
        entry = tmp_manager.recall("FAVORITE_GAME")
        assert entry is not None


# ---------------------------------------------------------------------------
# MemoryManager.search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_finds_by_key_substring(self, tmp_manager):
        tmp_manager.remember("favorite_game", "Minecraft")
        tmp_manager.remember("favorite_color", "blue")
        results = tmp_manager.search("favorite")
        assert len(results) == 2

    def test_finds_by_value_substring(self, tmp_manager):
        tmp_manager.remember("game", "Minecraft")
        tmp_manager.remember("activity", "cooking")
        results = tmp_manager.search("mine")
        assert len(results) == 1
        assert results[0]["key"] == "game"

    def test_empty_query_returns_empty(self, tmp_manager):
        tmp_manager.remember("game", "X")
        results = tmp_manager.search("")
        assert results == []

    def test_no_match_returns_empty(self, tmp_manager):
        tmp_manager.remember("game", "X")
        results = tmp_manager.search("zzznomatch")
        assert results == []


# ---------------------------------------------------------------------------
# MemoryManager.forget
# ---------------------------------------------------------------------------

class TestForget:
    def test_removes_existing_memory(self, tmp_manager):
        tmp_manager.remember("game", "Minecraft")
        removed = tmp_manager.forget("game")
        assert removed is True
        assert tmp_manager.recall("game") is None

    def test_returns_false_for_missing_key(self, tmp_manager):
        removed = tmp_manager.forget("does_not_exist")
        assert removed is False

    def test_only_removes_targeted_key(self, tmp_manager):
        tmp_manager.remember("game", "Minecraft")
        tmp_manager.remember("lang", "Python")
        tmp_manager.forget("game")
        assert tmp_manager.recall("lang") is not None

    def test_forget_then_remember_again(self, tmp_manager):
        tmp_manager.remember("game", "Minecraft")
        tmp_manager.forget("game")
        tmp_manager.remember("game", "Valorant")
        assert tmp_manager.recall("game")["value"] == "Valorant"


# ---------------------------------------------------------------------------
# MemoryManager.get_all
# ---------------------------------------------------------------------------

class TestGetAll:
    def test_returns_all_saved(self, tmp_manager):
        tmp_manager.remember("a", "1")
        tmp_manager.remember("b", "2")
        all_mem = tmp_manager.get_all()
        assert len(all_mem) == 2

    def test_empty_when_nothing_saved(self, tmp_manager):
        assert tmp_manager.get_all() == []

    def test_returns_copies_not_references(self, tmp_manager):
        tmp_manager.remember("x", "val")
        all_mem = tmp_manager.get_all()
        all_mem[0]["value"] = "MODIFIED"
        # Original should be unchanged
        assert tmp_manager.recall("x")["value"] == "val"


# ---------------------------------------------------------------------------
# Persistence / file format
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_file_created_on_init(self, tmp_path):
        path = tmp_path / "m.json"
        MemoryManager(path=path)
        assert path.exists()

    def test_file_format_is_correct(self, tmp_path):
        path = tmp_path / "m.json"
        m = MemoryManager(path=path)
        m.remember("game", "Minecraft")
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert "memories" in raw
        assert isinstance(raw["memories"], list)
        assert raw["memories"][0]["key"] == "game"

    def test_survives_corrupt_file(self, tmp_path):
        path = tmp_path / "m.json"
        path.write_text("NOT VALID JSON", encoding="utf-8")
        m = MemoryManager(path=path)
        # Should not crash; returns empty
        assert m.get_all() == []

    def test_survives_missing_file(self, tmp_path):
        path = tmp_path / "nonexistent" / "m.json"
        m = MemoryManager(path=path)
        assert m.get_all() == []
