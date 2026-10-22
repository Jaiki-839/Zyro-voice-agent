"""
devices/microphones.py — microphone enumeration/selection.

Required operations per skills/skill.md #18: enumerate, select, test,
get_current. Wraps `sounddevice` (PortAudio) so the rest of ZYRO never
imports it directly.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    import sounddevice as sd
except OSError:
    sd = None  # PortAudio not available on this system (e.g. this sandbox)


@dataclass(frozen=True)
class MicrophoneDevice:
    index: int
    name: str
    default_samplerate: float
    max_input_channels: int


class MicrophoneUnavailableError(RuntimeError):
    pass


def enumerate_microphones() -> list[MicrophoneDevice]:
    if sd is None:
        return []
    devices = sd.query_devices()
    result = []
    for idx, d in enumerate(devices):
        if d.get("max_input_channels", 0) > 0:
            result.append(
                MicrophoneDevice(
                    index=idx,
                    name=d["name"],
                    default_samplerate=d.get("default_samplerate", 16000.0),
                    max_input_channels=d["max_input_channels"],
                )
            )
    return result


def find_microphone(name_substring: str) -> MicrophoneDevice | None:
    needle = name_substring.strip().lower()
    if not needle:
        return None
    for mic in enumerate_microphones():
        if needle in mic.name.lower():
            return mic
    return None


def get_current_microphone() -> MicrophoneDevice | None:
    if sd is None:
        return None
    try:
        default_index = sd.default.device[0]
    except (TypeError, IndexError):
        return None
    if default_index is None or default_index < 0:
        return None
    for mic in enumerate_microphones():
        if mic.index == default_index:
            return mic
    return None


def select_microphone(name_substring: str) -> MicrophoneDevice:
    mic = find_microphone(name_substring)
    if mic is None:
        raise MicrophoneUnavailableError(f"No microphone matching '{name_substring}' was found.")
    if sd is not None:
        sd.default.device = (mic.index, sd.default.device[1] if isinstance(sd.default.device, (list, tuple)) else None)
    return mic
