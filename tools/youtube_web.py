"""
tools/youtube_web.py -- YouTube Web tools for ZYRO (with session context).

Wraps existing open_youtube() and search_youtube() from tools/web.py with
WebAppContext tracking so follow-up commands ("scroll", "go back", "search again")
continue working in the YouTube task context.

All URL construction is delegated to tools/web.py (webbrowser.open + URL-based).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("zyro.tools.youtube_web")


def _result(success: bool, message: str, data: Any = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data}


def open_youtube_webapp(mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Open YouTube in the browser and set it as the active web app.

    Delegates to tools/web.open_youtube() for the actual URL open.
    Updates session.webapp so follow-up commands are routed correctly.
    """
    from tools.web import open_youtube

    result = open_youtube(query="", mock_mode=mock_mode, session=session)
    if result.get("success") and session is not None:
        session.webapp.switch_app("youtube")
        d = result.get("data") or {}
        d["context"] = session.webapp.to_dict()
        result["data"] = d
        if mock_mode:
            result["message"] = "[mock] YouTube is open. What would you like me to do?"
        else:
            result["message"] = "YouTube is open. What would you like me to do?"
    return result


def search_youtube_webapp(query: str = "", mock_mode: bool = False, session=None, **_) -> dict[str, Any]:
    """
    Search YouTube and update the active web app context.

    Delegates to tools/web.search_youtube() for the URL.
    """
    from tools.web import search_youtube

    if not (query or "").strip():
        return _result(False, "A search query is required.", None)

    result = search_youtube(query=query, mock_mode=mock_mode, session=session)
    if result.get("success") and session is not None:
        session.webapp.update(
            active_app="youtube", last_action="search", active_target=query.strip(),
        )
        d = result.get("data") or {}
        d["context"] = session.webapp.to_dict()
        result["data"] = d
    return result
