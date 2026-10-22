"""
audio/microphone.py — captures mic input as an async stream of raw PCM
chunks, ready to hand to gemini/live_client.py's run_voice_session().

The rest of the application only depends on `stream_microphone()`; it does
not need to know sounddevice/PortAudio exists (skills/skill.md #17).
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from gemini.audio import CHANNELS, INPUT_SAMPLE_RATE

logger = logging.getLogger("zyro.audio.microphone")

_CHUNK_FRAMES = 1024  # frames per callback, ~64ms at 16kHz


class MicrophoneError(RuntimeError):
    pass


class MicrophoneSource:
    """Restartable mic capture so the Devices dialog can change the input
    device without tearing down the Gemini Live session."""

    def __init__(self, device_index: int | None = None) -> None:
        self.device_index = device_index
        self._loop: asyncio.AbstractEventLoop | None = None
        self._restart_event: asyncio.Event | None = None

    def set_device(self, device_index: int | None) -> None:
        self.device_index = device_index
        event = self._restart_event
        loop = self._loop
        if event is not None and loop is not None:
            loop.call_soon_threadsafe(event.set)
        logger.info("Microphone device set to %s", device_index if device_index is not None else "default")

    async def __aiter__(self) -> AsyncIterator[bytes]:
        self._loop = asyncio.get_running_loop()
        while True:
            self._restart_event = asyncio.Event()
            idx = self.device_index
            try:
                async for chunk in _capture_chunks(idx, self._restart_event):
                    yield chunk
            except asyncio.CancelledError:
                raise
            except MicrophoneError:
                logger.exception("Microphone stream failed; retrying")
                await asyncio.sleep(0.5)


async def _capture_chunks(device_index: int | None, restart: asyncio.Event) -> AsyncIterator[bytes]:
    try:
        import sounddevice as sd
    except OSError as exc:  # PortAudio missing/misconfigured
        raise MicrophoneError(f"Audio input device is unavailable: {exc}") from exc

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes] = asyncio.Queue()

    def _callback(indata, frames, time_info, status):  # noqa: ANN001 — sounddevice callback signature
        if status:
            logger.warning("Microphone stream status: %s", status)
        loop.call_soon_threadsafe(queue.put_nowait, bytes(indata))

    try:
        stream = sd.RawInputStream(
            samplerate=INPUT_SAMPLE_RATE,
            blocksize=_CHUNK_FRAMES,
            channels=CHANNELS,
            dtype="int16",
            device=device_index,
            callback=_callback,
        )
    except Exception as exc:  # noqa: BLE001
        raise MicrophoneError(f"Could not open microphone: {exc}") from exc

    with stream:
        logger.info("Microphone stream started (device=%s)", device_index if device_index is not None else "default")
        try:
            while not restart.is_set():
                get_task = asyncio.create_task(queue.get())
                wait_task = asyncio.create_task(restart.wait())
                done, pending = await asyncio.wait(
                    {get_task, wait_task}, return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
                if wait_task in done:
                    return
                yield get_task.result()
        finally:
            logger.info("Microphone stream stopped")


async def stream_microphone(
    device_index: int | None = None,
    source: MicrophoneSource | None = None,
) -> AsyncIterator[bytes]:
    """Yields raw 16-bit PCM mono chunks at 16kHz until cancelled."""
    src = source or MicrophoneSource(device_index)
    async for chunk in src:
        yield chunk


def test_microphone(device_index: int | None = None, duration_sec: float = 0.4) -> dict:
    """Blocking short capture used by the Devices dialog Test button."""
    try:
        import sounddevice as sd
    except OSError as exc:
        return {"success": False, "message": f"Audio input is unavailable: {exc}"}
    try:
        recording = sd.rec(
            int(duration_sec * INPUT_SAMPLE_RATE),
            samplerate=INPUT_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            device=device_index,
            blocking=True,
        )
        peak = int(max(abs(int(s[0])) for s in recording)) if len(recording) else 0
        if peak < 20:
            return {"success": True, "message": "Microphone opened, but the signal is very quiet.", "data": {"peak": peak}}
        return {"success": True, "message": f"Microphone is working (peak level {peak}).", "data": {"peak": peak}}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": f"Microphone test failed: {exc}"}
