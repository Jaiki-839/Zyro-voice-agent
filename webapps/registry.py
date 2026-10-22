"""
webapps/registry.py -- Supported web app definitions.

Adding a new web app:
  1. Add a WebApp entry to WEB_APP_REGISTRY.
  2. Create a tools/<appname>_web.py tool module.
  3. Register the tools in core/agent.py.
  4. Add tests.

No other core files need to change.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WebApp:
    """Definition of one supported web application."""

    # Canonical lowercase key used in WebAppContext.active_app
    name: str

    # Human-readable display name
    display_name: str

    # Primary URL to open when the user says "Open X"
    base_url: str

    # Substrings that typically appear in the browser window title when ready.
    # Used by wait_for_browser_ready() in browser_adapter.py.
    title_hints: tuple[str, ...] = field(default_factory=tuple)

    # URL template for search, if URL-based search is supported.
    # Use {query} as the placeholder; it will be URL-encoded.
    search_url_template: str | None = None

    # URL template for a profile/user page.
    # Use {username} as the placeholder.
    profile_url_template: str | None = None


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

WEB_APP_REGISTRY: dict[str, WebApp] = {
    "instagram": WebApp(
        name="instagram",
        display_name="Instagram",
        base_url="https://www.instagram.com/",
        title_hints=("Instagram",),
        search_url_template="https://www.instagram.com/explore/search/keyword/?q={query}",
        profile_url_template="https://www.instagram.com/{username}/",
    ),
    "discord": WebApp(
        name="discord",
        display_name="Discord",
        base_url="https://discord.com/app",
        title_hints=("Discord",),
        search_url_template=None,  # Discord uses in-app keyboard search (Ctrl+K)
        profile_url_template=None,
    ),
    "whatsapp": WebApp(
        name="whatsapp",
        display_name="WhatsApp Web",
        base_url="https://web.whatsapp.com/",
        title_hints=("WhatsApp",),
        search_url_template=None,  # WhatsApp uses in-app keyboard search
        profile_url_template=None,
    ),
    "youtube": WebApp(
        name="youtube",
        display_name="YouTube",
        base_url="https://www.youtube.com/",
        title_hints=("YouTube",),
        search_url_template="https://www.youtube.com/results?search_query={query}",
        profile_url_template=None,
    ),
    "spotify": WebApp(
        name="spotify",
        display_name="Spotify Web",
        base_url="https://open.spotify.com/",
        title_hints=("Spotify",),
        search_url_template="https://open.spotify.com/search/{query}",
        profile_url_template=None,
    ),
}


def get_app(name: str) -> WebApp | None:
    """Look up a WebApp by canonical name (case-insensitive)."""
    return WEB_APP_REGISTRY.get(name.lower().strip())


def list_apps() -> list[str]:
    """Return list of all supported app canonical names."""
    return list(WEB_APP_REGISTRY.keys())
