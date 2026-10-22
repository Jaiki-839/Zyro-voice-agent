"""
audio/playback.py — plays back raw PCM audio chunks received from Gemini.

Keeps a small internal output stream open and just accepts bytes; nothing
else in ZYRO needs to know the playback sample rate or backend.
"""
from __future__ import annotations

import logging
import math
import struct
import threading

from gemini.audio import CHANNELS, OUTPUT_SAMPLE_RATE

logger = logging.getLogger("zyro.audio.playback")


class AudioPlayer:
    def __init__(self, device_index: int | None = None) -> None:
        self._stream = None
        self._device_index = device_index
        self._lock = threading.Lock()

    def set_device(self, device_index: int | None) -> None:
        with self._lock:
            self._close_unlocked()
            self._device_index = device_index
        logger.info("Speaker device set to %s", device_index if device_index is not None else "default")

    def _ensure_stream(self):
        if self._stream is not None:
            return self._stream
        import sounddevice as sd

        self._stream = sd.RawOutputStream(
            samplerate=OUTPUT_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            device=self._device_index,
        )
        self._stream.start()
        return self._stream

    def play_chunk(self, pcm_bytes: bytes) -> None:
        try:
            with self._lock:
                stream = self._ensure_stream()
                stream.write(pcm_bytes)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to play audio chunk")

    def close(self) -> None:
        with self._lock:
            self._close_unlocked()

    def _close_unlocked(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:  # noqa: BLE001
                logger.debug("Error closing playback stream", exc_info=True)
            self._stream = None

    def play_test_tone(self, duration_sec: float = 0.35, hz: float = 440.0) -> dict:
        """Short sine burst for the Devices dialog Test Speaker button."""
        try:
            n = int(OUTPUT_SAMPLE_RATE * duration_sec)
            samples = [
                int(16000 * math.sin(2 * math.pi * hz * i / OUTPUT_SAMPLE_RATE))
                for i in range(n)
            ]
            pcm = struct.pack("<" + "h" * n, *samples)
            self.play_chunk(pcm)
            return {"success": True, "message": "Played a short test tone."}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "message": f"Speaker test failed: {exc}"}
