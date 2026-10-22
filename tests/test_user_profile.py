"""
tests/test_user_profile.py — unit tests for core/user_profile.py.

All tests use temporary files and monkeypatched env vars so they never
touch data/user_profile.json or read actual system env variables.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from core.user_profile import UserProfile, _DEFAULT_PROFILE_PATH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_profile_file(tmp_path):
    p = tmp_path / "user_profile.json"
    p.write_text(json.dumps({
        "user": {"name": "", "preferred_name": ""},
        "zyro": {"name": "ZYRO", "developer": "", "purpose": "...", "version": "0.1"},
    }), encoding="utf-8")
    return p


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all ZYRO_* env vars so tests start clean."""
    for var in [
        "ZYRO_NAME", "ZYRO_DEVELOPER", "ZYRO_PURPOSE", "ZYRO_VERSION",
        "ZYRO_USER_NAME", "ZYRO_USER_PREFERRED_NAME",
    ]:
        monkeypatch.delenv(var, raising=False)


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

class TestFileLoading:
    def test_loads_zyro_name_from_file(self, tmp_path, clean_env):
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({"zyro": {"name": "ZBot"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.zyro_name == "ZBot"

    def test_loads_user_name_from_file(self, tmp_path, clean_env):
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({"user": {"name": "Alice"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.user_name == "Alice"

    def test_loads_developer_from_file(self, tmp_path, clean_env):
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({"zyro": {"developer": "Jane Doe"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.developer == "Jane Doe"

    def test_survives_missing_file(self, tmp_path, clean_env):
        p = tmp_path / "nonexistent.json"
        profile = UserProfile(path=p)
        assert profile.zyro_name == "ZYRO"  # default
        assert profile.user_name == ""

    def test_survives_corrupt_json(self, tmp_path, clean_env):
        p = tmp_path / "profile.json"
        p.write_text("NOT JSON", encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.zyro_name == "ZYRO"

    def test_empty_file_uses_defaults(self, tmp_path, clean_env):
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.zyro_name == "ZYRO"
        assert profile.purpose == "Windows-first personal AI assistant"
        assert profile.version == "0.1"


# ---------------------------------------------------------------------------
# Env var override (env > file > default)
# ---------------------------------------------------------------------------

class TestEnvOverride:
    def test_env_overrides_file_zyro_name(self, tmp_path, monkeypatch, clean_env):
        monkeypatch.setenv("ZYRO_NAME", "MyBot")
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({"zyro": {"name": "FileBotName"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.zyro_name == "MyBot"

    def test_env_overrides_user_name(self, tmp_path, monkeypatch, clean_env):
        monkeypatch.setenv("ZYRO_USER_NAME", "Bob")
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({"user": {"name": "Alice"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.user_name == "Bob"

    def test_env_overrides_developer(self, tmp_path, monkeypatch, clean_env):
        monkeypatch.setenv("ZYRO_DEVELOPER", "EnvDev")
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({"zyro": {"developer": "FileDev"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.developer == "EnvDev"

    def test_env_overrides_purpose(self, tmp_path, monkeypatch, clean_env):
        monkeypatch.setenv("ZYRO_PURPOSE", "env purpose")
        profile = UserProfile(path=tmp_path / "x.json")
        assert profile.purpose == "env purpose"

    def test_env_overrides_version(self, tmp_path, monkeypatch, clean_env):
        monkeypatch.setenv("ZYRO_VERSION", "9.9")
        profile = UserProfile(path=tmp_path / "x.json")
        assert profile.version == "9.9"

    def test_env_preferred_name(self, tmp_path, monkeypatch, clean_env):
        monkeypatch.setenv("ZYRO_USER_PREFERRED_NAME", "Alex")
        profile = UserProfile(path=tmp_path / "x.json")
        assert profile.user_preferred_name == "Alex"


# ---------------------------------------------------------------------------
# Defaults — never invent missing info
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_developer_empty_by_default(self, tmp_path, clean_env):
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.developer == ""

    def test_user_name_empty_by_default(self, tmp_path, clean_env):
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.user_name == ""

    def test_zyro_name_defaults_to_ZYRO(self, tmp_path, clean_env):
        p = tmp_path / "profile.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert profile.zyro_name == "ZYRO"


# ---------------------------------------------------------------------------
# identity_context()
# ---------------------------------------------------------------------------

class TestIdentityContext:
    def test_includes_zyro_name(self, tmp_path, clean_env):
        p = tmp_path / "p.json"
        p.write_text(json.dumps({"zyro": {"name": "ZYRO"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        ctx = profile.identity_context()
        assert "ZYRO" in ctx

    def test_no_developer_says_not_configured(self, tmp_path, clean_env):
        p = tmp_path / "p.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        profile = UserProfile(path=p)
        ctx = profile.identity_context()
        assert "not been configured" in ctx.lower() or "hasn't been configured" in ctx.lower()

    def test_developer_present_is_mentioned(self, tmp_path, clean_env):
        p = tmp_path / "p.json"
        p.write_text(json.dumps({"zyro": {"developer": "Jane"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        ctx = profile.identity_context()
        assert "Jane" in ctx

    def test_user_name_present_is_mentioned(self, tmp_path, clean_env):
        p = tmp_path / "p.json"
        p.write_text(json.dumps({"user": {"name": "Alice"}}), encoding="utf-8")
        profile = UserProfile(path=p)
        ctx = profile.identity_context()
        assert "Alice" in ctx

    def test_no_user_name_says_not_saved(self, tmp_path, clean_env):
        p = tmp_path / "p.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        profile = UserProfile(path=p)
        ctx = profile.identity_context()
        assert "do not have" in ctx.lower() or "don't have" in ctx.lower()

    def test_does_not_invent_username_from_env(self, tmp_path, monkeypatch, clean_env):
        # Ensure Windows username (USERNAME env var) is NOT used
        monkeypatch.setenv("USERNAME", "WindowsUser")
        p = tmp_path / "p.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        profile = UserProfile(path=p)
        assert "WindowsUser" not in profile.identity_context()


# ---------------------------------------------------------------------------
# as_dict()
# ---------------------------------------------------------------------------

class TestAsDict:
    def test_shape(self, tmp_path, clean_env):
        p = tmp_path / "p.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        profile = UserProfile(path=p)
        d = profile.as_dict()
        assert "user" in d
        assert "zyro" in d
        assert "name" in d["user"]
        assert "name" in d["zyro"]
        assert "developer" in d["zyro"]
        assert "purpose" in d["zyro"]
        assert "version" in d["zyro"]
