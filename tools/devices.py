"""
tools/devices.py — list_audio_devices, select_audio_device,
list_camera_devices, select_camera_device.

Thin tool-layer wrappers around devices/microphones.py and devices/cameras.py.
Camera listing never turns the camera on — see devices/cameras.py.
"""
from __future__ import annotations

from typing import Any

from devices.cameras import enumerate_cameras, find_camera
from devices.microphones import (
    MicrophoneUnavailableError,
    enumerate_microphones,
    get_current_microphone,
    select_microphone,
)


def list_audio_devices(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    mics = enumerate_microphones()
    current = get_current_microphone()
    return {
        "success": True,
        "message": f"Found {len(mics)} microphone(s).",
        "data": {
            "results": [{"name": m.name, "index": m.index} for m in mics],
            "current": current.name if current else None,
        },
    }


def select_audio_device(name: str, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    if mock_mode:
        return {"success": True, "message": f"[mock] Would select microphone matching '{name}'.", "data": {"name": name}}
    try:
        mic = select_microphone(name)
    except MicrophoneUnavailableError as exc:
        return {"success": False, "message": str(exc), "data": None}
    return {"success": True, "message": f"Microphone set to {mic.name}.", "data": {"name": mic.name, "index": mic.index}}


def list_camera_devices(mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    cams = enumerate_cameras()
    return {
        "success": True,
        "message": f"Found {len(cams)} camera(s)." if cams else "No cameras were found (or OpenCV isn't installed).",
        "data": {"results": [{"name": c.name, "index": c.index} for c in cams]},
    }


def select_camera_device(name: str, mock_mode: bool = False, session=None, **_: Any) -> dict[str, Any]:
    if mock_mode:
        return {"success": True, "message": f"[mock] Would select camera matching '{name}'.", "data": {"name": name}}
    cam = find_camera(name)
    if cam is None:
        return {"success": False, "message": f"No camera matching '{name}' was found.", "data": None}
    return {"success": True, "message": f"Camera set to {cam.name}. It remains OFF until explicitly enabled.", "data": {"name": cam.name, "index": cam.index}}
