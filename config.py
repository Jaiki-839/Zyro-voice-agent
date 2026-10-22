"""
config.py — central configuration loader for ZYRO.

Every other module reads settings from here instead of touching os.environ
directly. This is the *only* place `.env` is loaded, and the only place that
is allowed to read GEMINI_API_KEY.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # loads .env if present; real environment variables always win


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _default_search_roots() -> list[Path]:
    """Reasonable default folders for file search on a Windows profile."""
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Pictures",
        home / "Music",
        home / "Videos",
    ]
    return [p for p in candidates if p.exists()] or [home]


@dataclass(frozen=True)
class ZyroConfig:
    zyro_name: str = field(default_factory=lambda: os.getenv("ZYRO_NAME", "ZYRO"))
    log_level: str = field(default_factory=lambda: os.getenv("ZYRO_LOG_LEVEL", "INFO").upper())
    mock_mode: bool = field(default_factory=lambda: _bool_env("ZYRO_MOCK_MODE", True))

    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.8-live"))

    default_mic: str = field(default_factory=lambda: os.getenv("ZYRO_DEFAULT_MIC", ""))
    default_speaker: str = field(default_factory=lambda: os.getenv("ZYRO_DEFAULT_SPEAKER", ""))
    default_camera: str = field(default_factory=lambda: os.getenv("ZYRO_DEFAULT_CAMERA", ""))

    # Identity / user profile (all optional — empty string means "not configured")
    zyro_developer: str = field(default_factory=lambda: os.getenv("ZYRO_DEVELOPER", "Jaiki Kushwaha"))
    zyro_purpose: str = field(default_factory=lambda: os.getenv("ZYRO_PURPOSE", "Windows-first personal AI assistant"))
    zyro_version: str = field(default_factory=lambda: os.getenv("ZYRO_VERSION", "0.1"))
    user_name: str = field(default_factory=lambda: os.getenv("ZYRO_USER_NAME", ""))
    user_preferred_name: str = field(default_factory=lambda: os.getenv("ZYRO_USER_PREFERRED_NAME", ""))

    search_roots: tuple[Path, ...] = field(default_factory=lambda: tuple(_default_search_roots()))

    def __post_init__(self) -> None:
        extra = os.getenv("ZYRO_EXTRA_SEARCH_ROOTS", "")
        if extra.strip():
            extra_paths = tuple(Path(p.strip()) for p in extra.split(",") if p.strip())
            object.__setattr__(self, "search_roots", self.search_roots + extra_paths)

    def require_api_key(self) -> str:
        """Raise a clear error if a live (non-mock) session is attempted without a key."""
        if not self.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in, "
                "or run with ZYRO_MOCK_MODE=true to develop without a live connection."
            )
        return self.gemini_api_key


CONFIG = ZyroConfig()


def persist_env_values(updates: dict[str, str], env_path: Path | None = None) -> None:
    """Update keys in `.env` without rewriting unrelated values or secrets."""
    path = env_path or Path(".env")
    lines: list[str] = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        key = stripped.split("=", 1)[0] if stripped and not stripped.startswith("#") and "=" in stripped else None
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            new_lines.append(line)
    for key, value in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def setup_logging(config: ZyroConfig = CONFIG) -> logging.Logger:
    """Configure ZYRO's logger. Never logs secrets — see core/tool_registry.py
    and gemini/live_client.py for the redaction rules applied before anything
    is written here."""
    logger = logging.getLogger("zyro")
    if logger.handlers:
        return logger  # already configured (e.g. re-imported in tests)

    logger.setLevel(getattr(logging, config.log_level, logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler("zyro.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
