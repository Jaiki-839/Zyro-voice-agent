"""
devices/speakers.py — playback-device enumeration/selection.

Mirrors devices/microphones.py so the UI Devices dialog can list output
devices without importing sounddevice directly.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    import sounddevice as sd
except OSError:
    sd = None


@dataclass(frozen=True)
class SpeakerDevice:
    index: int
    name: str
    default_samplerate: float
    max_output_channels: int


class SpeakerUnavailableError(RuntimeError):
    pass


def enumerate_speakers() -> list[SpeakerDevice]:
    if sd is None:
        return []
    devices = sd.query_devices()
    result = []
    for idx, d in enumerate(devices):
        if d.get("max_output_channels", 0) > 0:
            result.append(
                SpeakerDevice(
                    index=idx,
                    name=d["name"],
                    default_samplerate=d.get("default_samplerate", 24000.0),
                    max_output_channels=d["max_output_channels"],
                )
            )
    return result


def find_speaker(name_substring: str) -> SpeakerDevice | None:
    needle = name_substring.strip().lower()
    if not needle:
        return None
    for spk in enumerate_speakers():
        if needle in spk.name.lower():
            return spk
    return None


def get_current_speaker() -> SpeakerDevice | None:
    if sd is None:
        return None
    try:
        default_index = sd.default.device[1]
    except (TypeError, IndexError):
        return None
    if default_index is None or default_index < 0:
        return None
    for spk in enumerate_speakers():
        if spk.index == default_index:
            return spk
    return None


def select_speaker(name_substring: str) -> SpeakerDevice:
    spk = find_speaker(name_substring)
    if spk is None:
        raise SpeakerUnavailableError(f"No speaker matching '{name_substring}' was found.")
    if sd is not None:
        input_dev = sd.default.device[0] if isinstance(sd.default.device, (list, tuple)) else None
        sd.default.device = (input_dev, spk.index)
    return spk
