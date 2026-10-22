"""
tools/media_control.py -- System media control via Windows virtual key codes.

Uses ctypes keybd_event with the Windows media virtual key codes.  These are
system-level keys that control whatever app currently has media focus
(Spotify desktop, browser, Windows Media Player, etc.) without ZYRO needing
to know which app is playing.

"Play" means system PLAY -- it does NOT open YouTube or any other app.

Virtual key codes used (all from winuser.h):
  VK_MEDIA_NEXT_TRACK   0xB0
  VK_MEDIA_PREV_TRACK   0xB1
  VK_MEDIA_STOP         0xB2
  VK_MEDIA_PLAY_PAUSE   0xB3
  VK_VOLUME_MUTE        0xAD
  VK_VOLUME_DOWN        0xAE
  VK_VOLUME_UP          0xAF

media_play / media_pause are implemented as VK_MEDIA_PLAY_PAUSE because
Windows does not have separate VK_MEDIA_PLAY and VK_MEDIA_PAUSE keys --
the OS sends a toggle and the receiving app handles play vs pause logic.
"""
from __future__ import annotations

import ctypes
import logging
import sys
from typing import Any

logger = logging.getLogger("zyro.media")

if sys.platform == "win32":
    _user32 = ctypes.windll.user32  # type: ignore[attr-defined]
else:
    _user32 = None  # type: ignore[assignment]

# Windows media virtual key codes
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

KEYEVENTF_KEYUP = 0x0002


def _require_windows(name: str) -> dict[str, Any] | None:
    if sys.platform != "win32" or _user32 is None:
        return {"success": False, "message": f"'{name}' is only available on Windows.", "data": None}
    return None


def _tap(vk: int) -> None:
    """Press and immediately release a virtual key."""
    _user32.keybd_event(vk, 0, 0, 0)
    _user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def media_play(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Send the system PLAY media key.

    Note: Windows uses a single play/pause toggle key.  If media is already
    playing this will pause it -- the OS decides based on current state.
    Use media_play_pause if you want an explicit toggle.
    """
    err = _require_windows("media_play")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send media Play key.", "data": None}
    _tap(VK_MEDIA_PLAY_PAUSE)
    logger.info("VK_MEDIA_PLAY_PAUSE sent (media_play)")
    return {"success": True, "message": "Media play command sent.", "data": None}


def media_pause(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Send the system PAUSE media key."""
    err = _require_windows("media_pause")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send media Pause key.", "data": None}
    _tap(VK_MEDIA_PLAY_PAUSE)
    logger.info("VK_MEDIA_PLAY_PAUSE sent (media_pause)")
    return {"success": True, "message": "Media pause command sent.", "data": None}


def media_play_pause(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Toggle play/pause for the system media player."""
    err = _require_windows("media_play_pause")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send media Play/Pause key.", "data": None}
    _tap(VK_MEDIA_PLAY_PAUSE)
    logger.info("VK_MEDIA_PLAY_PAUSE sent (media_play_pause)")
    return {"success": True, "message": "Media play/pause toggled.", "data": None}


def media_next(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Skip to the next media track."""
    err = _require_windows("media_next")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send media Next Track key.", "data": None}
    _tap(VK_MEDIA_NEXT_TRACK)
    logger.info("VK_MEDIA_NEXT_TRACK sent (media_next)")
    return {"success": True, "message": "Skipped to the next track.", "data": None}


def media_previous(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Go back to the previous media track."""
    err = _require_windows("media_previous")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send media Previous Track key.", "data": None}
    _tap(VK_MEDIA_PREV_TRACK)
    logger.info("VK_MEDIA_PREV_TRACK sent (media_previous)")
    return {"success": True, "message": "Went to the previous track.", "data": None}


def media_volume_up(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Increase system volume."""
    err = _require_windows("media_volume_up")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send Volume Up key.", "data": None}
    _tap(VK_VOLUME_UP)
    logger.info("VK_VOLUME_UP sent (media_volume_up)")
    return {"success": True, "message": "Volume increased.", "data": None}


def media_volume_down(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Decrease system volume."""
    err = _require_windows("media_volume_down")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send Volume Down key.", "data": None}
    _tap(VK_VOLUME_DOWN)
    logger.info("VK_VOLUME_DOWN sent (media_volume_down)")
    return {"success": True, "message": "Volume decreased.", "data": None}


def media_mute(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Mute system audio."""
    err = _require_windows("media_mute")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send Mute key.", "data": None}
    _tap(VK_VOLUME_MUTE)
    logger.info("VK_VOLUME_MUTE sent (media_mute)")
    return {"success": True, "message": "System audio muted.", "data": None}


def media_unmute(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    """Unmute system audio (same key as mute -- toggles mute state)."""
    err = _require_windows("media_unmute")
    if err:
        return err
    if mock_mode:
        return {"success": True, "message": "[mock] Would send Mute (unmute) key.", "data": None}
    _tap(VK_VOLUME_MUTE)
    logger.info("VK_VOLUME_MUTE sent (media_unmute)")
    return {"success": True, "message": "System audio unmuted.", "data": None}
