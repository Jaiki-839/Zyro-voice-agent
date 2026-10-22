"""
devices/state.py — runtime mic/speaker/camera selection for the running agent.

This is the live counterpart to ZyroConfig's default device *name* strings.
The UI Devices dialog writes here; the microphone stream and AudioPlayer
read from here. Camera selection is stored but the camera stays OFF.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any

from devices.cameras import find_camera
from devices.microphones import find_microphone
from devices.speakers import find_speaker

logger = logging.getLogger("zyro.devices")

SYSTEM_DEFAULT_LABEL = "System default"


@dataclass
class DeviceState:
    mic_index: int | None = None
    mic_name: str = SYSTEM_DEFAULT_LABEL
    speaker_index: int | None = None
    speaker_name: str = SYSTEM_DEFAULT_LABEL
    camera_index: int | None = None
    camera_name: str | None = None
    camera_enabled: bool = False  # always False unless something explicit turns it on
    mic_generation: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)
    player: Any = None
    mic_source: Any = None

    @classmethod
    def from_config(cls, config) -> DeviceState:
        state = cls()
        if getattr(config, "default_mic", ""):
            mic = find_microphone(config.default_mic)
            if mic is not None:
                state.mic_index = mic.index
                state.mic_name = mic.name
        if getattr(config, "default_speaker", ""):
            spk = find_speaker(config.default_speaker)
            if spk is not None:
                state.speaker_index = spk.index
                state.speaker_name = spk.name
        if getattr(config, "default_camera", ""):
            cam = find_camera(config.default_camera)
            if cam is not None:
                state.camera_index = cam.index
                state.camera_name = cam.name
        return state

    def apply(
        self,
        mic_name: str | None = None,
        speaker_name: str | None = None,
        camera_name: str | None = None,
    ) -> dict[str, Any]:
        """Resolve names and push them into the live mic/player if attached."""
        with self.lock:
            if mic_name is not None:
                if not mic_name or mic_name == SYSTEM_DEFAULT_LABEL:
                    self.mic_index = None
                    self.mic_name = SYSTEM_DEFAULT_LABEL
                else:
                    mic = find_microphone(mic_name)
                    if mic is None:
                        return {"success": False, "message": f"No microphone matching '{mic_name}' was found."}
                    self.mic_index = mic.index
                    self.mic_name = mic.name
                self.mic_generation += 1
                if self.mic_source is not None:
                    self.mic_source.set_device(self.mic_index)

            if speaker_name is not None:
                if not speaker_name or speaker_name == SYSTEM_DEFAULT_LABEL:
                    self.speaker_index = None
                    self.speaker_name = SYSTEM_DEFAULT_LABEL
                else:
                    spk = find_speaker(speaker_name)
                    if spk is None:
                        return {"success": False, "message": f"No speaker matching '{speaker_name}' was found."}
                    self.speaker_index = spk.index
                    self.speaker_name = spk.name
                if self.player is not None:
                    self.player.set_device(self.speaker_index)

            if camera_name is not None:
                if not camera_name or camera_name in {SYSTEM_DEFAULT_LABEL, "No camera detected"}:
                    self.camera_index = None
                    self.camera_name = None
                else:
                    cam = find_camera(camera_name)
                    if cam is None:
                        return {"success": False, "message": f"No camera matching '{camera_name}' was found."}
                    self.camera_index = cam.index
                    self.camera_name = cam.name
                # Selection never enables capture.
                self.camera_enabled = False

        logger.info(
            "Devices applied (mic=%s, speaker=%s, camera=%s, camera_on=%s)",
            self.mic_name, self.speaker_name, self.camera_name or "none", self.camera_enabled,
        )
        return {
            "success": True,
            "message": "Devices applied.",
            "data": {
                "mic_index": self.mic_index,
                "mic_name": self.mic_name,
                "speaker_index": self.speaker_index,
                "speaker_name": self.speaker_name,
                "camera_index": self.camera_index,
                "camera_name": self.camera_name,
                "camera_enabled": self.camera_enabled,
            },
        }
