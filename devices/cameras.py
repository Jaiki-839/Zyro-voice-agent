"""
devices/cameras.py — camera enumeration/selection, including DroidCam.

DroidCam is treated as a normal Windows camera device, never a hard
dependency (master prompt section 13 / skills/skill.md #19). Camera is OFF
by default everywhere in ZYRO — nothing in this module captures a frame;
it only enumerates and names devices. Frame capture, if ever added, must be
gated behind an explicit, visible "camera is ON" state (see ui/devices.py).
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None  # optional dependency — camera tools degrade gracefully without it


@dataclass(frozen=True)
class CameraDevice:
    index: int
    name: str


def enumerate_cameras(max_probe: int = 10) -> list[CameraDevice]:
    """Best-effort enumeration. OpenCV doesn't expose device names portably,
    so devices are labeled generically; DroidCam appears like any other
    Windows camera once installed, per the requirement that it not be a
    hard dependency."""
    if cv2 is None:
        return []

    found: list[CameraDevice] = []
    for index in range(max_probe):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0)
        try:
            if cap is not None and cap.isOpened():
                found.append(CameraDevice(index=index, name=f"Camera {index}"))
        finally:
            if cap is not None:
                cap.release()
    return found


def find_camera(name_substring: str) -> CameraDevice | None:
    needle = name_substring.strip().lower()
    for cam in enumerate_cameras():
        if needle in cam.name.lower():
            return cam
    return None
