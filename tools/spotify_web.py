"""
tools/spotify_web.py -- Spotify Web tools for ZYRO (with session context).

Wraps existing open_spotify() and search_spotify() from tools/web.py with
WebAppContext tracking so follow-up commands continue in the Spotify context.

Playback note: These tools open a browser page only -- they do NOT start
audio playback. Spotify Web requires the user to be signed in. Never claim
playback started unless the tool result explicitly confirms it.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("zyro.tools.spotify_web")


def _result(success: bool, message: str, data: Any = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data}


def open_spotify_webapp(mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Open Spotify Web in the browser and set it as the active web app.

    Delegates to tools/web.open_spotify() for the URL open.
    Updates session.webapp for follow-up context.

    IMPORTANT: This opens the browser page only -- no playback is started.
    """
    from tools.web import open_spotify

    result = open_spotify(query="", mock_mode=mock_mode, session=session)
    if result.get("success") and session is not None:
        session.webapp.switch_app("spotify")
        d = result.get("data") or {}
        d["context"] = session.webapp.to_dict()
        result["data"] = d
        if mock_mode:
            result["message"] = "[mock] Spotify Web is open. What would you like me to do?"
        else:
            result["message"] = (
                "Spotify Web is open. What would you like me to do? "
                "(Note: playback requires you to be signed in.)"
            )
    return result


def search_spotify_webapp(query: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Search Spotify and update the active web app context.

    Delegates to tools/web.search_spotify() for the URL.
    Opens the Spotify search results page -- does not start playback.
    """
    from tools.web import search_spotify

    if not (query or "").strip():
        return _result(False, "A search query is required.", None)

    result = search_spotify(query=query, mock_mode=mock_mode, session=session)
    if result.get("success") and session is not None:
        session.webapp.update(
            active_app="spotify", last_action="search", active_target=query.strip(),
        )
        d = result.get("data") or {}
        d["context"] = session.webapp.to_dict()
        result["data"] = d
    return result
