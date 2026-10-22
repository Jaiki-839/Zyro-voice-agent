"""
tools/web.py — web search, URL opening, and webpage reading.

Tools in this module:
  web_search(query, max_results)  — search the web via DuckDuckGo HTML endpoint
  open_url(url)                   — open a validated http/https URL in the OS browser
  read_webpage(url)               — fetch + parse a public webpage into clean text
  open_youtube(query)             — open YouTube homepage or a search results page
  search_youtube(query)           — open a YouTube search results page
  open_spotify(query)             — open Spotify Web or a search results page
  search_spotify(query)           — open a Spotify search results page

Security rules (master prompt §11, §12, §20):
  • open_url only allows http:// and https:// — scheme validated with urllib.parse.
  • webbrowser.open() is used for all browser actions; no subprocess/shell involvement.
  • read_webpage uses requests with a 10 s timeout and a 2 MB response size cap.
  • No crawling — read_webpage reads exactly one URL per call.
  • All handlers follow the ToolDispatcher result convention exactly:
        {"success": bool, "message": str, "data": Any}

Web search backend:
  Default: DuckDuckGo HTML scraping (html.duckduckgo.com) — no API key required.
  Override: call register_search_backend(fn) to wire in a premium provider.
  mock_mode: every handler returns a safe "[mock] Would …" string without
             touching the network or the OS.
"""
from __future__ import annotations

import logging
import re
import urllib.parse
import webbrowser
from typing import Any, Callable

logger = logging.getLogger("zyro.tools.web")

# ---------------------------------------------------------------------------
# Pluggable search backend (optional premium override)
# ---------------------------------------------------------------------------

_search_backend: Callable[[str, int], list[dict[str, str]]] | None = None


def register_search_backend(fn: Callable[[str, int], list[dict[str, str]]]) -> None:
    """Wire in a real provider, e.g. SerpAPI or Bing Search.

    The callable must accept (query: str, max_results: int) and return a list
    of dicts, each with at least {"title": str, "url": str, "snippet": str}.
    """
    global _search_backend
    _search_backend = fn


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ALLOWED_SCHEMES = {"http", "https"}

# Scrub HTML tags from snippets so Gemini sees clean prose.
_TAG_RE = re.compile(r"<[^>]+>")


def _validate_url(url: str) -> tuple[bool, str]:
    """Return (ok, error_message). Only http/https pass."""
    url = url.strip()
    if not url:
        return False, "No URL was provided."
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False, "That doesn't appear to be a valid web URL."
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return False, (
            f"That doesn't appear to be a valid web URL. "
            f"Only http:// and https:// links are supported "
            f"(got scheme '{parsed.scheme or 'none'}')."
        )
    if not parsed.netloc:
        return False, "That doesn't appear to be a valid web URL (no domain found)."
    return True, ""


def _open_browser(url: str) -> None:
    """Open url in the OS default browser. Uses webbrowser — no shell."""
    webbrowser.open(url)


def _duckduckgo_search(query: str, max_results: int) -> list[dict[str, str]]:
    """Scrape DuckDuckGo HTML results (lite endpoint — no JS required).

    Returns a list of {"title", "url", "snippet", "source"} dicts.
    Raises on network error so the caller can wrap it.
    """
    import requests  # imported lazily — not required for mock/test paths

    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(search_url, headers=headers, timeout=12, allow_redirects=True)
    resp.raise_for_status()

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
    except ImportError:
        from bs4 import BeautifulSoup  # type: ignore[no-redef]
        soup = BeautifulSoup(resp.text, "html.parser")

    results: list[dict[str, str]] = []
    for result in soup.select(".result"):
        if len(results) >= max_results:
            break
        title_tag = result.select_one(".result__title a")
        snippet_tag = result.select_one(".result__snippet")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        raw_href = title_tag.get("href", "")
        # DDG wraps links in redirects — extract the real URL.
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
        url = qs.get("uddg", [raw_href])[0]
        snippet = _TAG_RE.sub("", snippet_tag.get_text(strip=True) if snippet_tag else "")
        try:
            source = urllib.parse.urlparse(url).netloc
        except Exception:
            source = ""
        if title and url:
            results.append({"title": title, "url": url, "snippet": snippet, "source": source})

    return results


# ---------------------------------------------------------------------------
# Tool 0 (modified existing): web_search
# ---------------------------------------------------------------------------

def web_search(
    query: str,
    max_results: int = 5,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Search the web for current information.

    Returns structured results: title, URL, snippet, source domain.
    Uses DuckDuckGo by default; falls back to any registered backend.
    """
    query = query.strip()
    if not query:
        return {"success": False, "message": "Please give me something to search for.", "data": None}

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would search the web for '{query}'.",
            "data": {
                "results": [
                    {
                        "title": f"Mock result for {query}",
                        "url": "https://example.com",
                        "snippet": f"This is a mock snippet about {query}.",
                        "source": "example.com",
                    }
                ]
            },
        }

    # Use registered premium backend if available.
    if _search_backend is not None:
        try:
            results = _search_backend(query, max_results)
            return {
                "success": True,
                "message": f"Found {len(results)} result(s) for '{query}'.",
                "data": {"results": results},
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Registered search backend failed: %s", exc)
            # Fall through to DuckDuckGo.

    # Default: DuckDuckGo.
    try:
        results = _duckduckgo_search(query, max_results)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DuckDuckGo search failed: %s", exc)
        return {
            "success": False,
            "message": f"Web search isn't available right now: {exc}",
            "data": None,
        }

    if not results:
        return {
            "success": False,
            "message": f"The web search returned no results for '{query}'.",
            "data": {"results": []},
        }

    return {
        "success": True,
        "message": f"Found {len(results)} result(s) for '{query}'.",
        "data": {"results": results},
    }


# ---------------------------------------------------------------------------
# Tool 1 (new): open_url
# ---------------------------------------------------------------------------

def open_url(
    url: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Open a validated http/https URL in the OS default browser.

    Only http:// and https:// URLs are accepted. file://, javascript:,
    data:, vbscript:, and all other schemes are rejected. No shell
    execution — uses webbrowser.open() exclusively.
    """
    url = url.strip()
    ok, err = _validate_url(url)
    if not ok:
        return {"success": False, "message": err, "data": None}

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would open {url} in the default browser.",
            "data": {"url": url},
        }

    try:
        _open_browser(url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("open_url failed for %s: %s", url, exc)
        return {"success": False, "message": f"Failed to open the URL: {exc}", "data": None}

    return {
        "success": True,
        "message": f"Opened {url} in the default browser.",
        "data": {"url": url},
    }


# ---------------------------------------------------------------------------
# Tool 2 (new): read_webpage
# ---------------------------------------------------------------------------

_READ_TIMEOUT_SEC = 10
_READ_MAX_BYTES = 2 * 1024 * 1024   # 2 MB
_READ_MAX_TEXT = 8_000               # chars sent back to Gemini


def read_webpage(
    url: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Fetch a public webpage and extract its readable text content.

    Returns {"title": str, "text": str, "url": str, "truncated": bool}.
    Handles HTTP errors, timeouts, and JS-only pages honestly.
    """
    url = url.strip()
    ok, err = _validate_url(url)
    if not ok:
        return {"success": False, "message": err, "data": None}

    if mock_mode:
        return {
            "success": True,
            "message": f"[mock] Would read the webpage at {url}.",
            "data": {"title": "Mock Page", "text": f"Mock content from {url}.", "url": url, "truncated": False},
        }

    import requests  # lazily imported

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = requests.get(
            url,
            headers=headers,
            timeout=_READ_TIMEOUT_SEC,
            allow_redirects=True,
            stream=True,
        )
        resp.raise_for_status()

        # Size-limit the download.
        chunks: list[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=65536):
            chunks.append(chunk)
            total += len(chunk)
            if total >= _READ_MAX_BYTES:
                break
        raw_html = b"".join(chunks).decode(resp.encoding or "utf-8", errors="replace")

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": f"The request to {url} timed out. The page may be slow or unreachable.",
            "data": None,
        }
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        return {
            "success": False,
            "message": f"The page returned an HTTP {status} error.",
            "data": None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("read_webpage network error for %s: %s", url, exc)
        return {
            "success": False,
            "message": f"Could not fetch the page: {exc}",
            "data": None,
        }

    # Parse HTML -> clean text.
    try:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_html, "lxml")
        except ImportError:
            from bs4 import BeautifulSoup  # type: ignore[no-redef]
            soup = BeautifulSoup(raw_html, "html.parser")
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "message": f"I opened the page but couldn't parse its content: {exc}",
            "data": None,
        }

    # Remove noise elements.
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "noscript", "iframe"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    body = soup.get_text(separator="\n", strip=True)

    # Collapse excessive blank lines.
    lines = [ln for ln in body.splitlines() if ln.strip()]
    text = "\n".join(lines)

    if not text.strip():
        return {
            "success": False,
            "message": (
                "I opened the page, but couldn't extract readable text. "
                "The page may require JavaScript or a login to display content."
            ),
            "data": {"title": title, "url": url},
        }

    truncated = len(text) > _READ_MAX_TEXT
    if truncated:
        text = text[:_READ_MAX_TEXT] + "\n... [content truncated]"

    return {
        "success": True,
        "message": f"Read '{title or url}' successfully.",
        "data": {"title": title, "text": text, "url": url, "truncated": truncated},
    }


# ---------------------------------------------------------------------------
# Tools 3 & 4 (new): open_youtube / search_youtube
# ---------------------------------------------------------------------------

_YOUTUBE_BASE = "https://www.youtube.com"
_YOUTUBE_SEARCH = "https://www.youtube.com/results?search_query={}"


def open_youtube(
    query: str = "",
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Open YouTube in the default browser.

    No query -> YouTube homepage.
    With query -> YouTube search results page for that query.
    This opens the browser page only — no playback is started.
    """
    query = (query or "").strip()
    if query:
        url = _YOUTUBE_SEARCH.format(urllib.parse.quote_plus(query))
        action = f"Opened YouTube search for '{query}'. The results page is now open in your browser."
        mock_msg = f"[mock] Would open YouTube search for '{query}'."
    else:
        url = _YOUTUBE_BASE
        action = "Opened the YouTube homepage in your browser."
        mock_msg = "[mock] Would open YouTube homepage."

    if mock_mode:
        return {"success": True, "message": mock_msg, "data": {"url": url, "query": query}}

    result = open_url(url, mock_mode=False)
    if result["success"]:
        return {"success": True, "message": action, "data": {"url": url, "query": query}}
    return result


def search_youtube(
    query: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Search YouTube for a query and open the results page.

    This opens the YouTube search results page in your browser only —
    no playback is started.
    """
    return open_youtube(query=query, mock_mode=mock_mode, session=session)


# ---------------------------------------------------------------------------
# Tools 5 & 6 (new): open_spotify / search_spotify
# ---------------------------------------------------------------------------

_SPOTIFY_BASE = "https://open.spotify.com"
_SPOTIFY_SEARCH = "https://open.spotify.com/search/{}"


def open_spotify(
    query: str = "",
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Open Spotify Web in the default browser.

    No query -> Spotify Web homepage.
    With query -> Spotify search results page for that query.
    Spotify Web requires login; if not signed in, the login page will appear.
    This opens the browser page only — no playback is started.
    """
    query = (query or "").strip()
    if query:
        url = _SPOTIFY_SEARCH.format(urllib.parse.quote_plus(query))
        action = (
            f"Opened Spotify search for '{query}'. "
            "The search results are now open in your browser. "
            "Spotify Web requires you to be signed in to play music."
        )
        mock_msg = f"[mock] Would open Spotify search for '{query}'."
    else:
        url = _SPOTIFY_BASE
        action = (
            "Opened Spotify Web in your browser. "
            "Spotify Web requires you to be signed in."
        )
        mock_msg = "[mock] Would open Spotify Web homepage."

    if mock_mode:
        return {"success": True, "message": mock_msg, "data": {"url": url, "query": query}}

    result = open_url(url, mock_mode=False)
    if result["success"]:
        return {"success": True, "message": action, "data": {"url": url, "query": query}}
    return result


def search_spotify(
    query: str,
    mock_mode: bool = False,
    session=None,
    **_: Any,
) -> dict[str, Any]:
    """Search Spotify for a query and open the Spotify search results page.

    This opens the Spotify Web search page in your browser only —
    no playback is started. Spotify Web requires login to play music.
    """
    return open_spotify(query=query, mock_mode=mock_mode, session=session)
