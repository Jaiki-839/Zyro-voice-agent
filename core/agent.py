"""
core/agent.py — top-level ZYRO agent: builds the tool registry, wires up
the dispatcher, and runs either a voice or text session against Gemini
Live.

app.py is a thin CLI shell around this module.
"""
from __future__ import annotations

import asyncio
import logging

from audio.wake_detector import build_wake_detector
from config import CONFIG, ZyroConfig, setup_logging
from core.permissions import PermissionLevel
from core.router import ToolDispatcher
from core.session import SessionContext
from core.tool_registry import Tool, ToolParameter, ToolRegistry
from core.user_profile import UserProfile
from core.zyro_state import StateManager
from devices.state import DeviceState
from gemini.live_client import LiveClient
from memory.memory import MemoryManager
from tools import applications, devices, files, terminal, web
from tools.browser_control import (
    close_browser_tab,
    next_browser_tab,
    open_new_browser_tab,
    previous_browser_tab,
    switch_to_browser_tab,
)
from tools.desktop_control import (
    close_window,
    focus_application,
    maximize_window,
    minimize_window,
    restore_window,
    switch_app,
)
from tools.media_control import (
    media_mute,
    media_next,
    media_pause,
    media_play,
    media_play_pause,
    media_previous,
    media_unmute,
    media_volume_down,
    media_volume_up,
)
from tools.memory_tools import (
    forget_memory,
    recall_memory,
    remember_memory,
    search_memory,
)
from tools.web import (
    open_spotify,
    open_url,
    open_youtube,
    read_webpage,
    search_spotify,
    search_youtube,
)
from tools.windows_system import (
    open_special_folder,
    open_system_utility,
    open_windows_settings,
)

logger = logging.getLogger("zyro.agent")


def _make_sleep_handler():
    """Returns a zyro_sleep handler closed over the StateManager.

    The handler is updated with the real state_manager after ZyroAgent is
    initialised via the ``_state_manager`` attribute that is injected below.
    This avoids a circular dependency between build_registry and ZyroAgent.
    """
    # We use a mutable container so the closure reference can be updated later.
    _ref: list = [None]  # _ref[0] = StateManager | None

    def _sleep_handler(mock_mode: bool = False, session=None, **_):
        mgr = _ref[0]
        if mock_mode:
            return {"success": True, "message": "[mock] ZYRO would enter sleep mode.", "data": None}
        if mgr is not None:
            mgr.set_sleeping()
        return {"success": True, "message": "Going to sleep. Say 'Hey ZYRO, wake up' to resume.", "data": None}

    _sleep_handler._ref = _ref  # expose so ZyroAgent can inject the real mgr
    return _sleep_handler


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(Tool(
        name="open_application",
        description="Open/launch a desktop application by name, e.g. 'Chrome' or 'VS Code'.",
        permission=PermissionLevel.SAFE,
        handler=applications.open_application,
        parameters=(ToolParameter("name", "string", "Name of the application to open."),),
    ))
    registry.register(Tool(
        name="list_applications",
        description="List applications ZYRO knows how to open.",
        permission=PermissionLevel.SAFE,
        handler=applications.list_applications,
        parameters=(),
    ))
    registry.register(Tool(
        name="search_files",
        description="Search for files by name across the user's known folders (Desktop, Documents, Downloads, etc).",
        permission=PermissionLevel.SAFE,
        handler=files.search_files,
        parameters=(
            ToolParameter("query", "string", "Filename or partial filename to search for."),
            ToolParameter("extension", "string", "Optional file extension filter, e.g. 'pdf'.", required=False, default=""),
            ToolParameter("max_results", "integer", "Maximum number of results to return.", required=False, default=20),
        ),
    ))
    registry.register(Tool(
        name="get_file_info",
        description="Get filename, path, extension, size, and modified time for a specific file.",
        permission=PermissionLevel.SAFE,
        handler=files.get_file_info,
        parameters=(ToolParameter("path", "string", "Full path to the file."),),
    ))
    registry.register(Tool(
        name="open_file",
        description="Open a file with its default application.",
        permission=PermissionLevel.SAFE,
        handler=files.open_file,
        parameters=(ToolParameter("path", "string", "Full path to the file to open."),),
    ))
    registry.register(Tool(
        name="open_folder",
        description="Open a folder in File Explorer.",
        permission=PermissionLevel.SAFE,
        handler=files.open_folder,
        parameters=(ToolParameter("path", "string", "Full path to the folder to open."),),
    ))
    registry.register(Tool(
        name="create_folder",
        description="Create a new folder at the given path.",
        permission=PermissionLevel.SAFE,
        handler=files.create_folder,
        parameters=(ToolParameter("path", "string", "Full path of the folder to create."),),
    ))
    registry.register(Tool(
        name="reveal_in_explorer",
        description="Reveal (highlight) a file or folder in File Explorer.",
        permission=PermissionLevel.SAFE,
        handler=files.reveal_in_explorer,
        parameters=(ToolParameter("path", "string", "Full path to reveal."),),
    ))
    registry.register(Tool(
        name="open_terminal",
        description="Open a terminal/command-line window, optionally in a specific folder.",
        permission=PermissionLevel.SAFE,
        handler=terminal.open_terminal,
        parameters=(ToolParameter("cwd", "string", "Folder to open the terminal in.", required=False, default=""),),
    ))
    registry.register(Tool(
        name="list_audio_devices",
        description="List available microphones.",
        permission=PermissionLevel.SAFE,
        handler=devices.list_audio_devices,
        parameters=(),
    ))
    registry.register(Tool(
        name="select_audio_device",
        description="Select which microphone ZYRO should use.",
        permission=PermissionLevel.SAFE,
        handler=devices.select_audio_device,
        parameters=(ToolParameter("name", "string", "Microphone name or a substring of it."),),
    ))
    registry.register(Tool(
        name="list_camera_devices",
        description="List available cameras, including DroidCam if installed.",
        permission=PermissionLevel.SAFE,
        handler=devices.list_camera_devices,
        parameters=(),
    ))
    registry.register(Tool(
        name="select_camera_device",
        description="Select which camera ZYRO should use. This does not turn the camera on.",
        permission=PermissionLevel.SAFE,
        handler=devices.select_camera_device,
        parameters=(ToolParameter("name", "string", "Camera name or a substring of it."),),
    ))
    registry.register(Tool(
        name="web_search",
        description=(
            "Search the web for current or external information. "
            "Use this when the user explicitly asks to 'search the web', 'look up', 'find', or 'search for' something, "
            "or when they need information that may have changed recently (news, latest versions, current events). "
            "Do NOT use this for stable general knowledge questions you can answer directly. "
            "Returns a list of results with title, URL, snippet, and source domain."
        ),
        permission=PermissionLevel.SAFE,
        handler=web.web_search,
        parameters=(
            ToolParameter("query", "string", "The search query to look up on the web."),
            ToolParameter("max_results", "integer", "Maximum number of results to return.", required=False, default=5),
        ),
    ))
    registry.register(Tool(
        name="open_url",
        description=(
            "Open a specific http or https URL in the user's default web browser. "
            "Use this when the user says 'open [URL]', 'go to [website]', or 'open this link'. "
            "Only http:// and https:// URLs are accepted — all other schemes are rejected for safety."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_url,
        parameters=(
            ToolParameter("url", "string", "A valid http:// or https:// URL to open in the browser."),
        ),
    ))
    registry.register(Tool(
        name="read_webpage",
        description=(
            "Fetch a public webpage and extract its readable text content. "
            "Use this when the user asks to 'read', 'summarize', or 'tell me what this page says' about a URL. "
            "Also use this after a web_search when you need to read the full content of a result. "
            "Returns the page title and readable text. Handles errors honestly — "
            "if the page requires JavaScript or login, it will say so."
        ),
        permission=PermissionLevel.SAFE,
        handler=read_webpage,
        parameters=(
            ToolParameter("url", "string", "A valid http:// or https:// URL of the webpage to read."),
        ),
    ))
    registry.register(Tool(
        name="open_youtube",
        description=(
            "Open YouTube in the default browser. "
            "With no query, opens the YouTube homepage. "
            "With a query, opens a YouTube search results page for that query. "
            "Use this when the user says 'open YouTube', 'go to YouTube', 'play [X] on YouTube', "
            "or 'search YouTube for [X]'. "
            "IMPORTANT: This only opens the browser page — it does NOT start audio or video playback. "
            "Tell the user the search results page was opened, never say a video is playing."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_youtube,
        parameters=(
            ToolParameter("query", "string", "Optional search query for YouTube. Leave empty to open the homepage.", required=False, default=""),
        ),
    ))
    registry.register(Tool(
        name="search_youtube",
        description=(
            "Search YouTube for a query and open the search results page in the browser. "
            "Use this when the user explicitly says 'search YouTube for [X]' or 'find [X] on YouTube'. "
            "IMPORTANT: This only opens the search results page — no playback is started."
        ),
        permission=PermissionLevel.SAFE,
        handler=search_youtube,
        parameters=(
            ToolParameter("query", "string", "The search query to look up on YouTube."),
        ),
    ))
    registry.register(Tool(
        name="open_spotify",
        description=(
            "Open Spotify Web in the default browser. "
            "With no query, opens the Spotify Web homepage. "
            "With a query, opens a Spotify search results page for that query. "
            "Use this when the user says 'open Spotify', 'find [X] on Spotify', or 'play [X] on Spotify'. "
            "IMPORTANT: This only opens the browser page — it does NOT start audio playback. "
            "Spotify Web requires the user to be signed in. Tell the user the search page was opened."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_spotify,
        parameters=(
            ToolParameter("query", "string", "Optional search query for Spotify. Leave empty to open the homepage.", required=False, default=""),
        ),
    ))
    registry.register(Tool(
        name="search_spotify",
        description=(
            "Search Spotify for a query and open the Spotify search results page in the browser. "
            "Use this when the user says 'search Spotify for [X]' or 'find [X] on Spotify'. "
            "IMPORTANT: This only opens the search results page — no playback is started. "
            "Spotify Web requires the user to be signed in."
        ),
        permission=PermissionLevel.SAFE,
        handler=search_spotify,
        parameters=(
            ToolParameter("query", "string", "The search query to look up on Spotify."),
        ),
    ))
    registry.register(Tool(
        name="remember_memory",
        description=(
            "Save or update a named memory. "
            "ONLY call this when the user explicitly says to 'remember', 'save', 'store', "
            "'keep in memory', or 'don't forget' something. "
            "Never call this during normal conversation — only on explicit save requests. "
            "Rejects secrets such as passwords, API keys, and tokens. "
            "If a memory with the same key already exists, it is updated — no duplicate created."
        ),
        permission=PermissionLevel.SAFE,
        handler=remember_memory,
        parameters=(
            ToolParameter("key", "string", "Short label for the memory (e.g. 'favorite_game', 'preferred_language')."),
            ToolParameter("value", "string", "The value to remember (e.g. 'Minecraft', 'Python')."),
        ),
    ))
    registry.register(Tool(
        name="recall_memory",
        description=(
            "Retrieve a specific saved memory by key. "
            "Use this when the user asks about something they previously asked you to remember. "
            "If nothing is found, return an honest 'not saved' result — never fabricate a memory."
        ),
        permission=PermissionLevel.SAFE,
        handler=recall_memory,
        parameters=(
            ToolParameter("key", "string", "The memory key to look up (e.g. 'favorite_game')."),
        ),
    ))
    registry.register(Tool(
        name="search_memory",
        description=(
            "Search all saved memories for keys or values matching a query string. "
            "Use when the user asks 'what do you remember about me?' or 'what have I saved?'. "
            "Never fabricate results — only return what is actually stored."
        ),
        permission=PermissionLevel.SAFE,
        handler=search_memory,
        parameters=(
            ToolParameter("query", "string", "Substring to search for in memory keys and values."),
        ),
    ))
    registry.register(Tool(
        name="forget_memory",
        description=(
            "Remove a saved memory by key. "
            "Use when the user says 'forget [X]' or 'delete [X] from memory'. "
            "Returns an honest result if the key was not found."
        ),
        permission=PermissionLevel.SAFE,
        handler=forget_memory,
        parameters=(
            ToolParameter("key", "string", "The memory key to remove (e.g. 'favorite_game')."),
        ),
    ))

    # -----------------------------------------------------------------------
    # Desktop control tools
    # -----------------------------------------------------------------------
    registry.register(Tool(
        name="close_window",
        description=(
            "Close a window by its application name, or close the currently active window. "
            "Say 'close Chrome', 'close this', 'close the window'. "
            "Sends WM_CLOSE -- the application can refuse (e.g. unsaved document). "
            "Does NOT forcefully terminate processes."
        ),
        permission=PermissionLevel.SAFE,
        handler=close_window,
        parameters=(
            ToolParameter("app_name", "string", "Name of the app whose window to close. Leave empty to close the active window.", required=False, default=""),
        ),
    ))
    registry.register(Tool(
        name="switch_app",
        description=(
            "Switch to the previous application using Alt+Tab. "
            "Use when the user says 'switch app', 'go back', 'previous window', 'Alt+Tab'."
        ),
        permission=PermissionLevel.SAFE,
        handler=switch_app,
        parameters=(),
    ))
    registry.register(Tool(
        name="minimize_window",
        description=(
            "Minimize a window. Use when the user says 'minimize this', 'minimize Chrome', 'hide this window'. "
            "If no app_name is given, minimizes the active window."
        ),
        permission=PermissionLevel.SAFE,
        handler=minimize_window,
        parameters=(
            ToolParameter("app_name", "string", "Application name to minimize. Leave empty for active window.", required=False, default=""),
        ),
    ))
    registry.register(Tool(
        name="maximize_window",
        description=(
            "Maximize a window. Use when the user says 'maximize this', 'maximize Chrome', 'make it full screen'. "
            "If no app_name is given, maximizes the active window."
        ),
        permission=PermissionLevel.SAFE,
        handler=maximize_window,
        parameters=(
            ToolParameter("app_name", "string", "Application name to maximize. Leave empty for active window.", required=False, default=""),
        ),
    ))
    registry.register(Tool(
        name="restore_window",
        description=(
            "Restore a minimized or maximized window to its normal size. "
            "Use when the user says 'restore this', 'unminimize', 'restore window'. "
            "If no app_name is given, restores the active window."
        ),
        permission=PermissionLevel.SAFE,
        handler=restore_window,
        parameters=(
            ToolParameter("app_name", "string", "Application name to restore. Leave empty for active window.", required=False, default=""),
        ),
    ))
    registry.register(Tool(
        name="focus_application",
        description=(
            "Bring an existing application window to the foreground without launching it. "
            "Use when the user says 'switch to Chrome', 'bring Chrome to front', 'focus VS Code'. "
            "If the app is not already open, tell the user and suggest open_application."
        ),
        permission=PermissionLevel.SAFE,
        handler=focus_application,
        parameters=(
            ToolParameter("app_name", "string", "Name of the application window to bring to the foreground."),
        ),
    ))

    # -----------------------------------------------------------------------
    # Browser tab control tools
    # -----------------------------------------------------------------------
    registry.register(Tool(
        name="next_browser_tab",
        description="Switch to the next browser tab (Ctrl+Tab). Use for 'next tab'.",
        permission=PermissionLevel.SAFE,
        handler=next_browser_tab,
        parameters=(),
    ))
    registry.register(Tool(
        name="previous_browser_tab",
        description="Switch to the previous browser tab (Ctrl+Shift+Tab). Use for 'previous tab', 'go back a tab'.",
        permission=PermissionLevel.SAFE,
        handler=previous_browser_tab,
        parameters=(),
    ))
    registry.register(Tool(
        name="close_browser_tab",
        description="Close the current browser tab (Ctrl+W). Use for 'close this tab', 'close tab'.",
        permission=PermissionLevel.SAFE,
        handler=close_browser_tab,
        parameters=(),
    ))
    registry.register(Tool(
        name="open_new_browser_tab",
        description="Open a new browser tab (Ctrl+T). Use for 'new tab', 'open a new tab'.",
        permission=PermissionLevel.SAFE,
        handler=open_new_browser_tab,
        parameters=(),
    ))
    registry.register(Tool(
        name="switch_to_browser_tab",
        description=(
            "Switch to a specific browser tab by number 1-9 (Ctrl+1..Ctrl+9). "
            "Use for 'switch to tab 3', 'go to first tab', 'switch to last tab'. "
            "Tab 9 selects the last tab in most browsers."
        ),
        permission=PermissionLevel.SAFE,
        handler=switch_to_browser_tab,
        parameters=(
            ToolParameter("tab_number", "integer", "Tab number to switch to (1-9). Use 9 for the last tab."),
        ),
    ))

    # -----------------------------------------------------------------------
    # Media control tools
    # -----------------------------------------------------------------------
    registry.register(Tool(
        name="media_play",
        description="Send the system Play media key. Use for 'play', 'resume'. Does NOT open YouTube or any app.",
        permission=PermissionLevel.SAFE,
        handler=media_play,
        parameters=(),
    ))
    registry.register(Tool(
        name="media_pause",
        description="Send the system Pause media key. Use for 'pause'.",
        permission=PermissionLevel.SAFE,
        handler=media_pause,
        parameters=(),
    ))
    registry.register(Tool(
        name="media_play_pause",
        description="Toggle system media play/pause. Use for 'play/pause', 'toggle playback'.",
        permission=PermissionLevel.SAFE,
        handler=media_play_pause,
        parameters=(),
    ))
    registry.register(Tool(
        name="media_next",
        description="Skip to the next media track. Use for 'next song', 'next track', 'skip'.",
        permission=PermissionLevel.SAFE,
        handler=media_next,
        parameters=(),
    ))
    registry.register(Tool(
        name="media_previous",
        description="Go to the previous media track. Use for 'previous song', 'go back a song'.",
        permission=PermissionLevel.SAFE,
        handler=media_previous,
        parameters=(),
    ))
    registry.register(Tool(
        name="media_volume_up",
        description="Increase system volume. Use for 'volume up', 'louder', 'turn it up'.",
        permission=PermissionLevel.SAFE,
        handler=media_volume_up,
        parameters=(),
    ))
    registry.register(Tool(
        name="media_volume_down",
        description="Decrease system volume. Use for 'volume down', 'quieter', 'turn it down'.",
        permission=PermissionLevel.SAFE,
        handler=media_volume_down,
        parameters=(),
    ))
    registry.register(Tool(
        name="media_mute",
        description="Mute system audio. Use for 'mute', 'silence', 'mute audio'.",
        permission=PermissionLevel.SAFE,
        handler=media_mute,
        parameters=(),
    ))
    registry.register(Tool(
        name="media_unmute",
        description="Unmute system audio. Use for 'unmute', 'turn sound back on'.",
        permission=PermissionLevel.SAFE,
        handler=media_unmute,
        parameters=(),
    ))

    # -----------------------------------------------------------------------
    # Windows system tools
    # -----------------------------------------------------------------------
    registry.register(Tool(
        name="open_windows_settings",
        description=(
            "Open a Windows Settings page. "
            "Supported categories: bluetooth, network, wifi, ethernet, display, sound, apps, "
            "windows_update, personalization, storage, privacy, camera, microphone, location, "
            "notifications, accounts, time, gaming, accessibility, security, power, multitasking, "
            "about, keyboard, mouse, touchpad, printers, devices. "
            "Examples: 'open Bluetooth settings', 'open display settings', 'open WiFi settings'."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_windows_settings,
        parameters=(
            ToolParameter(
                "category", "string",
                "Settings category (e.g. 'bluetooth', 'display', 'sound', 'windows_update')."
            ),
        ),
    ))
    registry.register(Tool(
        name="open_system_utility",
        description=(
            "Open a Windows system utility. "
            "Supported: task_manager, device_manager, control_panel, cmd, powershell, "
            "file_explorer, regedit. "
            "Examples: 'open Task Manager', 'open Device Manager', 'open Control Panel'."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_system_utility,
        parameters=(
            ToolParameter(
                "utility", "string",
                "Utility name (e.g. 'task_manager', 'device_manager', 'control_panel')."
            ),
        ),
    ))
    registry.register(Tool(
        name="open_special_folder",
        description=(
            "Open a known Windows folder in File Explorer. "
            "Supported: downloads, documents, desktop, pictures, videos, music, recycle_bin, home. "
            "Examples: 'open Downloads', 'open Documents', 'open Recycle Bin'."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_special_folder,
        parameters=(
            ToolParameter(
                "folder", "string",
                "Folder name (e.g. 'downloads', 'documents', 'recycle_bin')."
            ),
        ),
    ))

    # -----------------------------------------------------------------------
    # Sleep tool (internal -- Gemini calls this to enter sleep mode)
    # -----------------------------------------------------------------------
    registry.register(Tool(
        name="zyro_sleep",
        description=(
            "Put ZYRO into sleep mode. ONLY call this when the user explicitly says: "
            "'sleep', 'go to sleep', 'ZYRO sleep', 'sleep mode', 'Hey ZYRO sleep'. "
            "Do NOT call during normal conversation. "
            "While sleeping, ZYRO stops processing voice and tool commands. "
            "The user must say 'Hey ZYRO, wake up' or type 'wake up' to resume."
        ),
        permission=PermissionLevel.SAFE,
        handler=_make_sleep_handler(),
        parameters=(),
    ))

    # -----------------------------------------------------------------------
    # Web App Agent V2 tools
    # -----------------------------------------------------------------------
    from tools.instagram import (
        open_instagram,
        search_instagram,
        open_instagram_profile,
        open_instagram_reels,
        open_instagram_post,
        refresh_instagram,
    )
    from tools.discord_web import (
        open_discord,
        open_discord_server,
        open_discord_channel,
        search_discord,
        send_discord_message,
    )
    from tools.whatsapp_web import (
        open_whatsapp,
        search_whatsapp_contact,
        open_whatsapp_contact,
        send_whatsapp_message,
    )
    from tools.webapp_nav import (
        scroll_webapp,
        go_back_webapp,
        go_forward_webapp,
        refresh_webapp,
    )
    from tools.youtube_web import open_youtube_webapp, search_youtube_webapp
    from tools.spotify_web import open_spotify_webapp, search_spotify_webapp

    # Instagram
    registry.register(Tool(
        name="open_instagram",
        description=(
            "Open Instagram in the default browser. "
            "Use for: 'open Instagram', 'go to Instagram'. "
            "After opening, ask what the user wants to do next. "
            "Sets Instagram as the active web app for follow-up commands."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_instagram,
        parameters=(),
    ))
    registry.register(Tool(
        name="search_instagram",
        description=(
            "Search Instagram by opening a URL-based search page. "
            "Use for: 'search xyz on Instagram', 'find the Instagram ID xyz', "
            "'search an ID' (when Instagram is active). "
            "Constructs a validated, URL-encoded search URL internally -- "
            "never accepts raw URLs from Gemini."
        ),
        permission=PermissionLevel.SAFE,
        handler=search_instagram,
        parameters=(
            ToolParameter("query", "string", "The Instagram username or keyword to search for."),
        ),
    ))
    registry.register(Tool(
        name="open_instagram_profile",
        description=(
            "Open an Instagram profile page. "
            "Use for: 'open their profile', 'open xyz profile', 'open the profile'. "
            "If username is empty, uses the active Instagram target from context. "
            "Constructs a validated URL internally: https://www.instagram.com/<username>/"
        ),
        permission=PermissionLevel.SAFE,
        handler=open_instagram_profile,
        parameters=(
            ToolParameter(
                "username", "string",
                "Instagram username. Leave empty to use the active target from context.",
                required=False, default="",
            ),
        ),
    ))
    registry.register(Tool(
        name="open_instagram_reels",
        description=(
            "Open the Reels section for an Instagram profile. "
            "Use for: 'open reels', 'show me reels', 'open their reels'. "
            "If username is empty, uses the active Instagram target from context."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_instagram_reels,
        parameters=(
            ToolParameter(
                "username", "string",
                "Instagram username. Leave empty to use the active target from context.",
                required=False, default="",
            ),
        ),
    ))
    registry.register(Tool(
        name="open_instagram_post",
        description=(
            "Navigate to the posts grid for an Instagram profile. "
            "Use for: 'open their posts', 'show posts', 'open post'. "
            "If username is empty, uses the active Instagram target from context."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_instagram_post,
        parameters=(
            ToolParameter(
                "username", "string",
                "Instagram username. Leave empty to use the active target from context.",
                required=False, default="",
            ),
        ),
    ))
    registry.register(Tool(
        name="refresh_instagram",
        description="Refresh the current Instagram page (F5). Use for: 'refresh Instagram'.",
        permission=PermissionLevel.SAFE,
        handler=refresh_instagram,
        parameters=(),
    ))

    # Discord
    registry.register(Tool(
        name="open_discord",
        description=(
            "Open Discord Web (discord.com/app) in the browser. "
            "Use for: 'open Discord', 'go to Discord'. "
            "After opening, ask what the user wants to do next."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_discord,
        parameters=(),
    ))
    registry.register(Tool(
        name="open_discord_server",
        description=(
            "Navigate to a Discord server using Ctrl+K quick search. "
            "Use for: 'open server General', 'go to the Gaming server'. "
            "Discord must be open in the browser."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_discord_server,
        parameters=(
            ToolParameter("server_name", "string", "The Discord server name to navigate to."),
        ),
    ))
    registry.register(Tool(
        name="open_discord_channel",
        description=(
            "Navigate to a Discord channel using Ctrl+K quick search. "
            "Use for: 'find General', 'go to the general channel', 'open channel'. "
            "Discord must be open in the browser."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_discord_channel,
        parameters=(
            ToolParameter("channel_name", "string", "The Discord channel name to navigate to."),
        ),
    ))
    registry.register(Tool(
        name="search_discord",
        description=(
            "Search Discord using Ctrl+K quick search (servers, channels, users). "
            "Use for: 'search Discord for General', 'find user xyz in Discord'."
        ),
        permission=PermissionLevel.SAFE,
        handler=search_discord,
        parameters=(
            ToolParameter("query", "string", "The search query for Discord quick search."),
        ),
    ))
    registry.register(Tool(
        name="send_discord_message",
        description=(
            "Type and send a message in the currently active Discord channel. "
            "REQUIRES EXPLICIT USER CONFIRMATION before sending. "
            "Use for: 'send hello', 'say hi in Discord'. "
            "Discord must be open and a channel must be selected. "
            "The confirmation token fingerprints the exact message text -- "
            "changing the message requires a new confirmation."
        ),
        permission=PermissionLevel.CONFIRM,
        handler=send_discord_message,
        parameters=(
            ToolParameter("message", "string", "The exact message text to send."),
        ),
    ))

    # WhatsApp
    registry.register(Tool(
        name="open_whatsapp",
        description=(
            "Open WhatsApp Web (web.whatsapp.com) in the browser. "
            "Use for: 'open WhatsApp', 'go to WhatsApp'. "
            "After opening, ask what the user wants to do next. "
            "Note: requires QR code login if not previously authenticated."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_whatsapp,
        parameters=(),
    ))
    registry.register(Tool(
        name="search_whatsapp_contact",
        description=(
            "Search for a WhatsApp contact using the WhatsApp search panel (Ctrl+F). "
            "Use for: 'search for Shlok on WhatsApp', 'find a contact'. "
            "Does NOT automatically open the contact -- shows results for user review. "
            "If multiple contacts match, ask the user which one."
        ),
        permission=PermissionLevel.SAFE,
        handler=search_whatsapp_contact,
        parameters=(
            ToolParameter("contact_name", "string", "The contact name to search for."),
        ),
    ))
    registry.register(Tool(
        name="open_whatsapp_contact",
        description=(
            "Search for and open a WhatsApp contact. "
            "Use for: 'message Shlok', 'open Shlok on WhatsApp'. "
            "Only use when the contact name is unambiguous. "
            "If multiple contacts might match, use search_whatsapp_contact first."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_whatsapp_contact,
        parameters=(
            ToolParameter("contact_name", "string", "The contact name to find and open."),
        ),
    ))
    registry.register(Tool(
        name="send_whatsapp_message",
        description=(
            "Send a WhatsApp message to a contact. "
            "REQUIRES EXPLICIT USER CONFIRMATION before sending. "
            "Use for: 'send hiii to Shlok', 'message Shlok saying hello'. "
            "The confirmation token fingerprints both contact_name AND message -- "
            "changing either requires a new confirmation. "
            "Never claim success if the browser action fails."
        ),
        permission=PermissionLevel.CONFIRM,
        handler=send_whatsapp_message,
        parameters=(
            ToolParameter(
                "contact_name", "string",
                "Contact name. Leave empty to use the active WhatsApp contact from context.",
                required=False, default="",
            ),
            ToolParameter("message", "string", "The exact message text to send."),
        ),
    ))

    # Shared webapp navigation
    registry.register(Tool(
        name="scroll_webapp",
        description=(
            "Scroll the currently active web app page. "
            "Use for: 'scroll down', 'scroll up', 'scroll', 'scroll a bit', 'scroll more'. "
            "direction: 'up' or 'down'. amount: 'small', 'medium', or 'large'. "
            "No arbitrary scroll amounts are accepted."
        ),
        permission=PermissionLevel.SAFE,
        handler=scroll_webapp,
        parameters=(
            ToolParameter(
                "direction", "string", "Scroll direction.",
                required=False, default="down", enum=("up", "down"),
            ),
            ToolParameter(
                "amount", "string", "Scroll amount.",
                required=False, default="medium", enum=("small", "medium", "large"),
            ),
            ToolParameter(
                "app", "string",
                "Optional: override which app to scroll. Defaults to session active app.",
                required=False, default="",
            ),
        ),
    ))
    registry.register(Tool(
        name="go_back_webapp",
        description=(
            "Go back in the browser (Alt+Left) on the current web app page. "
            "Use for: 'go back', 'back', 'previous page', 'go back to the profile'."
        ),
        permission=PermissionLevel.SAFE,
        handler=go_back_webapp,
        parameters=(
            ToolParameter(
                "app", "string", "Optional app name override.",
                required=False, default="",
            ),
        ),
    ))
    registry.register(Tool(
        name="go_forward_webapp",
        description=(
            "Go forward in the browser (Alt+Right). "
            "Use for: 'go forward', 'forward'."
        ),
        permission=PermissionLevel.SAFE,
        handler=go_forward_webapp,
        parameters=(
            ToolParameter(
                "app", "string", "Optional app name override.",
                required=False, default="",
            ),
        ),
    ))
    registry.register(Tool(
        name="refresh_webapp",
        description=(
            "Refresh the current web app page (F5). "
            "Use for: 'refresh', 'reload', 'refresh the page'."
        ),
        permission=PermissionLevel.SAFE,
        handler=refresh_webapp,
        parameters=(
            ToolParameter(
                "app", "string", "Optional app name override.",
                required=False, default="",
            ),
        ),
    ))

    # YouTube webapp
    registry.register(Tool(
        name="open_youtube_webapp",
        description=(
            "Open YouTube in the browser and set it as the active web app. "
            "Use for: 'open YouTube', 'go to YouTube'. "
            "After opening, ask what the user wants to do next. "
            "Sets YouTube as the active web app for follow-up commands like 'scroll' or 'go back'."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_youtube_webapp,
        parameters=(),
    ))
    registry.register(Tool(
        name="search_youtube_webapp",
        description=(
            "Search YouTube and track the active web app context. "
            "Use for: 'search YouTube for Minecraft', 'find Python tutorials on YouTube' "
            "(when YouTube is already the active app, 'search Minecraft' also works). "
            "Does NOT start playback -- opens the search results page only."
        ),
        permission=PermissionLevel.SAFE,
        handler=search_youtube_webapp,
        parameters=(
            ToolParameter("query", "string", "The YouTube search query."),
        ),
    ))

    # Spotify webapp
    registry.register(Tool(
        name="open_spotify_webapp",
        description=(
            "Open Spotify Web in the browser and set it as the active web app. "
            "Use for: 'open Spotify', 'go to Spotify'. "
            "After opening, ask what the user wants to do next. "
            "Note: playback requires the user to be signed in. "
            "This tool opens the browser page only -- no playback is started."
        ),
        permission=PermissionLevel.SAFE,
        handler=open_spotify_webapp,
        parameters=(),
    ))
    registry.register(Tool(
        name="search_spotify_webapp",
        description=(
            "Search Spotify and track the active web app context. "
            "Use for: 'search Spotify for Arijit Singh', 'find songs on Spotify'. "
            "Opens the Spotify search results page only -- no playback is started. "
            "Spotify Web requires the user to be signed in."
        ),
        permission=PermissionLevel.SAFE,
        handler=search_spotify_webapp,
        parameters=(
            ToolParameter("query", "string", "The Spotify search query."),
        ),
    ))

    return registry


class ZyroAgent:
    def __init__(self, config: ZyroConfig = CONFIG) -> None:
        self.config = config
        setup_logging(config)

        # Memory and identity -- initialised before registry so tools can use them.
        self.memory = MemoryManager()
        self.profile = UserProfile()

        # Centralized sleep/wake state machine (starts ACTIVE, never persisted).
        self.state_manager = StateManager()

        # Local wake detector (used while sleeping to detect wake phrases locally
        # without sending audio to Gemini).
        self.wake_detector = build_wake_detector()
        if not self.wake_detector.available:
            logger.warning(
                "Voice wake detection unavailable. Text-mode wake ('wake up') still works."
            )

        self.registry = build_registry()
        self.session = SessionContext()
        # Attach the MemoryManager to the session so tool handlers can reach it.
        self.session.memory = self.memory  # type: ignore[attr-defined]

        # Inject the real StateManager into the zyro_sleep handler closure.
        sleep_tool = self.registry.get("zyro_sleep")
        if sleep_tool is not None:
            sleep_tool.handler._ref[0] = self.state_manager

        self.dispatcher = ToolDispatcher(
            registry=self.registry,
            session=self.session,
            mock_mode=config.mock_mode,
            state_manager=self.state_manager,
        )
        self.live_client = LiveClient(
            config,
            self.dispatcher,
            profile=self.profile,
            state_manager=self.state_manager,
            wake_detector=self.wake_detector,
        )
        self.device_state = DeviceState.from_config(config)
        logger.info(
            "%s initialized (%d tools, mock_mode=%s, model=%s)",
            config.zyro_name, len(self.registry.all()), config.mock_mode, config.gemini_model,
        )

    async def run_voice(
        self,
        on_text_out=None,
        on_user_text=None,
        on_status=None,
        on_tool=None,
    ) -> None:
        from audio.microphone import MicrophoneSource, stream_microphone
        from audio.playback import AudioPlayer

        player = AudioPlayer(device_index=self.device_state.speaker_index)
        source = MicrophoneSource(device_index=self.device_state.mic_index)
        self.device_state.player = player
        self.device_state.mic_source = source
        try:
            await self.live_client.run_voice_session(
                stream_microphone(source=source),
                on_audio_out=player.play_chunk,
                on_text_out=on_text_out,
                on_user_text=on_user_text,
                on_status=on_status,
                on_tool=on_tool,
            )
        finally:
            self.device_state.player = None
            self.device_state.mic_source = None
            player.close()

    async def run_text(self) -> None:
        """Console dev-mode: type instead of speak, ZYRO's spoken replies are
        printed as transcript text. Requires a real GEMINI_API_KEY even
        though no audio hardware is used."""

        async def _stdin_lines():
            loop = asyncio.get_event_loop()
            while True:
                line = await loop.run_in_executor(None, input, "you> ")
                if line.strip().lower() in {"quit", "exit"}:
                    return
                yield line

        def _print_zyro(text: str) -> None:
            print(f"{self.config.zyro_name}> {text}")

        await self.live_client.run_text_session(_stdin_lines(), on_text_out=_print_zyro)
