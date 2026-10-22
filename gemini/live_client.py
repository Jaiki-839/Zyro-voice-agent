"""
gemini/live_client.py — thin wrapper around the official Google GenAI SDK's
Live API session.

Follows the connect/send/receive pattern from the official docs
(ai.google.dev/gemini-api/docs/live-api/get-started-sdk). Everything
ZYRO-specific (tool dispatch, permissions, logging) lives elsewhere; this
module's only job is talking to Gemini.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator, Callable

from config import ZyroConfig
from core.router import ToolDispatcher
from gemini.function_calls import handle_tool_call
from gemini.session_config import build_live_config

logger = logging.getLogger("zyro.live_client")

STARTUP_GREETING = "Hello sir, how can I help you?"
STARTUP_GREETING_PROMPT = (
    f'Speak this greeting now, and nothing else: "{STARTUP_GREETING}"'
)
_GREETING_LISTEN_TIMEOUT_SEC = 15.0

StatusCallback = Callable[[str], None]
TextCallback = Callable[[str], None]
ToolCallback = Callable[[str, dict[str, Any]], None]


class LiveClient:
    """
    Manages one Gemini Live session for ZYRO.

    Usage:
        client = LiveClient(config, dispatcher)
        await client.run_voice_session(audio_in_stream, on_audio_out)

    or, for text-only development/testing:
        await client.run_text_session()
    """

    def __init__(
        self,
        config: ZyroConfig,
        dispatcher: ToolDispatcher,
        profile=None,
        state_manager=None,  # core.zyro_state.StateManager | None
        wake_detector=None,  # audio.wake_detector.WakeDetector | None
    ) -> None:
        self.config = config
        self.dispatcher = dispatcher
        self.profile = profile  # UserProfile | None
        self._state_manager = state_manager
        self._wake_detector = wake_detector
        self._text_queue: asyncio.Queue[str] | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._suppress_mic = False
        self._last_typed: str | None = None

    def submit_text(self, text: str) -> bool:
        """Enqueue a typed message onto the *current* Live session (thread-safe)."""
        cleaned = (text or "").strip()
        if not cleaned or self._text_queue is None or self._loop is None:
            return False
        loop = self._loop
        queue = self._text_queue

        def _put() -> None:
            self._last_typed = cleaned
            self._suppress_mic = True
            queue.put_nowait(cleaned)

        try:
            loop.call_soon_threadsafe(_put)
            logger.info("Typed message queued for Gemini Live")
            return True
        except RuntimeError:
            return False

    def _client(self):
        from google import genai  # imported lazily — not required for mock/text-only unit tests

        return genai.Client(api_key=self.config.require_api_key())

    async def _receive_loop(
        self,
        session: Any,
        on_audio_out=None,
        on_text_out: TextCallback | None = None,
        on_user_text: TextCallback | None = None,
        on_status: StatusCallback | None = None,
        on_turn_complete: Callable[[], None] | None = None,
        on_tool: ToolCallback | None = None,
    ) -> None:
        # session.receive() yields one complete model turn, then ends.
        # After a tool call, turn_complete can arrive before the spoken
        # follow-up — without an outer loop the receiver dies and later
        # user messages are sent but never answered.
        while True:
            playback_active = False
            async for response in session.receive():
                if getattr(response, "tool_call", None):
                    if on_status:
                        on_status("Running tool")
                    for fc in response.tool_call.function_calls:
                        if on_tool:
                            on_tool(fc.name, dict(fc.args or {}))
                    await handle_tool_call(session, self.dispatcher, response.tool_call)
                    logger.info("Gemini Live session still active after tool call")
                    if on_status:
                        on_status("Listening")
                    continue

                content = getattr(response, "server_content", None)
                if content is None:
                    continue

                if content.input_transcription and content.input_transcription.text:
                    text = content.input_transcription.text
                    logger.info("User said: %s", text)
                    last = self._last_typed
                    if last and (text.strip() == last or text.strip() in last or last in text.strip()):
                        pass
                    elif on_user_text:
                        on_user_text(text)

                if content.output_transcription and content.output_transcription.text:
                    text = content.output_transcription.text
                    logger.info("ZYRO said: %s", text)
                    if on_text_out:
                        on_text_out(text)

                if content.model_turn and on_audio_out is not None:
                    for part in content.model_turn.parts:
                        if getattr(part, "inline_data", None):
                            if not playback_active:
                                logger.info("Audio playback started")
                                playback_active = True
                                self._suppress_mic = True
                                if on_status:
                                    on_status("Speaking")
                            on_audio_out(part.inline_data.data)

                if getattr(content, "turn_complete", False):
                    if playback_active:
                        logger.info("Audio playback completed")
                        playback_active = False
                    logger.info("Voice response received")
                    self._suppress_mic = False
                    self._last_typed = None
                    if on_status:
                        on_status("Listening")
                    if on_turn_complete:
                        on_turn_complete()

    async def run_voice_session(
        self,
        audio_chunks: AsyncIterator[bytes],
        on_audio_out=None,
        on_text_out: TextCallback | None = None,
        on_user_text: TextCallback | None = None,
        on_status: StatusCallback | None = None,
        on_tool: ToolCallback | None = None,
    ) -> None:
        """Full voice pipeline: mic chunks in, native audio out.
        Typed messages submitted via submit_text() share this same session."""
        from google.genai import types

        config = build_live_config(self.config, self.dispatcher.registry, profile=self.profile)
        client = self._client()

        async with client.aio.live.connect(model=self.config.gemini_model, config=config) as session:
            logger.info("Gemini Live session started (voice mode)")
            if on_status:
                on_status("Connected")

            self._loop = asyncio.get_running_loop()
            self._text_queue = asyncio.Queue()
            greeting_done = asyncio.Event()
            self._suppress_mic = True

            def _mark_greeting_done() -> None:
                if not greeting_done.is_set():
                    greeting_done.set()

            async def _send_audio() -> None:
                it = audio_chunks.__aiter__()
                try:
                    first_chunk = await it.__anext__()
                except StopAsyncIteration:
                    return

                logger.info("Microphone listening")
                await session.send_realtime_input(text=STARTUP_GREETING_PROMPT)
                logger.info("Voice greeting sent")
                if on_status:
                    on_status("Speaking")

                try:
                    await asyncio.wait_for(greeting_done.wait(), timeout=_GREETING_LISTEN_TIMEOUT_SEC)
                except asyncio.TimeoutError:
                    logger.warning("Startup greeting did not finish in time; continuing to listen")
                    greeting_done.set()

                del first_chunk
                self._suppress_mic = False
                if on_status:
                    on_status("Listening")

                async for chunk in it:
                    if self._suppress_mic:
                        continue
                    # Sleep gate: while sleeping, route audio to local wake
                    # detector ONLY -- never send sleeping audio to Gemini.
                    if self._state_manager is not None and self._state_manager.is_sleeping():
                        if self._wake_detector is not None:
                            try:
                                woke = self._wake_detector.process_audio(chunk)
                            except Exception:  # noqa: BLE001
                                woke = False
                            if woke:
                                logger.info("Wake phrase detected locally -- resuming")
                                self._state_manager.set_active()
                                if on_status:
                                    on_status("Listening")
                        continue  # don't forward to Gemini
                    await session.send_realtime_input(
                        audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                    )

            async def _send_typed() -> None:
                assert self._text_queue is not None
                while True:
                    line = await self._text_queue.get()
                    self._suppress_mic = True
                    await session.send_realtime_input(text=line)
                    logger.info("Typed message sent to Gemini Live")

            try:
                await asyncio.gather(
                    _send_audio(),
                    _send_typed(),
                    self._receive_loop(
                        session,
                        on_audio_out=on_audio_out,
                        on_text_out=on_text_out,
                        on_user_text=on_user_text,
                        on_status=on_status,
                        on_turn_complete=_mark_greeting_done,
                        on_tool=on_tool,
                    ),
                )
            finally:
                self._text_queue = None
                self._loop = None

    async def run_text_session(self, text_input: AsyncIterator[str], on_text_out=None) -> None:
        """Text-only session -- useful for development without a microphone,
        and for automated testing of the tool-calling path against the real
        API. Response modality is still audio per the model's defaults; if
        `on_text_out` is given, output transcription is forwarded to it.

        Sleep/wake is detected locally from text before forwarding to Gemini:
          - Sleep phrases ("sleep", "go to sleep", etc.) -> set SLEEPING
          - Wake phrases ("wake up", etc.) while SLEEPING -> set ACTIVE
          - All other text while SLEEPING -> blocked (not sent to Gemini)
        """
        from audio.wake_detector import text_is_sleep_phrase, text_is_wake_phrase

        config = build_live_config(self.config, self.dispatcher.registry, profile=self.profile)
        client = self._client()

        async with client.aio.live.connect(model=self.config.gemini_model, config=config) as session:
            logger.info("Gemini Live session started (text mode)")

            async def _send_text() -> None:
                async for line in text_input:
                    mgr = self._state_manager
                    stripped = line.strip()

                    if mgr is not None and mgr.is_sleeping():
                        # While sleeping: only local wake detection, no Gemini
                        if text_is_wake_phrase(stripped):
                            logger.info("Text wake phrase detected")
                            mgr.set_active()
                            if on_text_out:
                                on_text_out("I'm awake. How can I help you?")
                        else:
                            if on_text_out:
                                on_text_out("I'm sleeping. Say 'wake up' to resume.")
                        continue  # do NOT forward to Gemini while sleeping

                    # While active: detect explicit sleep commands locally as
                    # a belt-and-suspenders check (Gemini also calls zyro_sleep).
                    if mgr is not None and text_is_sleep_phrase(stripped):
                        logger.info("Text sleep phrase detected locally")
                        mgr.set_sleeping()
                        if on_text_out:
                            on_text_out("Going to sleep. Say 'wake up' to resume.")
                        continue  # don't echo the sleep command to Gemini

                    await session.send_realtime_input(text=line)

            async def _receive_with_text() -> None:
                await self._receive_loop(session, on_audio_out=None, on_text_out=on_text_out)

            await asyncio.gather(_send_text(), _receive_with_text())
