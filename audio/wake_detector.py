"""
audio/wake_detector.py -- Local wake-word detection abstraction.

This module provides a clean interface for detecting wake phrases WITHOUT
sending audio to Gemini.  In SLEEPING state, the live_client passes mic
chunks here instead of to Gemini Live.

V1 ships two implementations:

  NullWakeDetector
      Always returns False.  Safe no-op when no local engine is available.
      available = False.

  KeywordWakeDetector
      Uses Windows SAPI (win32com/ISpSharedRecognizer) for local speech
      recognition.  Falls back to NullWakeDetector if SAPI is unavailable.
      available = True if SAPI initialised successfully.

The interface is stable so Porcupine / openWakeWord / Whisper can be plugged
in later by subclassing WakeDetector and passing an instance to LiveClient.

Wake phrases (matched case-insensitively, substring):
  - "wake up"
  - "hey zyro"
  - "zyro wake"
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("zyro.wake")

# Wake phrases -- lowercase substrings that trigger wake detection.
# Any recognised speech containing one of these triggers a wake.
WAKE_PHRASES: tuple[str, ...] = (
    "wake up",
    "hey zyro",
    "zyro wake",
    "wake up zyro",
)


def _matches_wake(text: str) -> bool:
    """Return True if the recognised text contains a wake phrase."""
    lowered = text.lower()
    return any(phrase in lowered for phrase in WAKE_PHRASES)


class WakeDetector(ABC):
    """Abstract base for local wake-word detectors."""

    available: bool = False

    @abstractmethod
    def process_audio(self, chunk: bytes) -> bool:
        """Process one raw PCM audio chunk (16-bit, 16 kHz, mono).

        Returns True if a wake phrase was detected in this chunk.
        Must never raise -- swallow errors and return False.
        """

    def close(self) -> None:
        """Optional cleanup.  Called when the mic pipeline shuts down."""


class NullWakeDetector(WakeDetector):
    """No-op detector -- always returns False.  Used when no engine is available."""

    available: bool = False

    def process_audio(self, chunk: bytes) -> bool:  # noqa: ARG002
        return False


class KeywordWakeDetector(WakeDetector):
    """
    V1 SAPI-based local wake detector for Windows.

    Uses the Windows Speech Recognition shared recognizer via SAPI
    (win32com.client).  Audio chunks are written to a buffer; when SAPI
    fires a recognition event the result is checked against WAKE_PHRASES.

    If SAPI is not available (non-Windows, missing win32com, or COM error),
    this falls back gracefully with available=False.

    Limitations of V1:
      - SAPI recognition is asynchronous; there can be up to ~1s latency.
      - The shared recognizer may conflict with other SAPI apps.
      - For production wake-word detection, replace with Porcupine or
        openWakeWord by subclassing WakeDetector.
    """

    available: bool = False

    def __init__(self) -> None:
        self._wake_flag = False
        try:
            self._init_sapi()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "SAPI wake detector unavailable (%s). "
                "Wake detection will only work in text mode. "
                "Install pywin32 and ensure Windows Speech Recognition is "
                "enabled, or plug in a dedicated wake-word engine.",
                exc,
            )

    def _init_sapi(self) -> None:
        """Attempt to initialise SAPI.  Raises on failure."""
        import win32com.client  # type: ignore[import]
        import pythoncom  # type: ignore[import]

        pythoncom.CoInitialize()
        self._recognizer = win32com.client.Dispatch("SAPI.SpSharedRecognizer")
        context = self._recognizer.CreateRecoContext()
        grammar = context.CreateGrammar()
        grammar.DictationSetState(1)  # free dictation

        # Register event handler
        self._sapi_events = win32com.client.WithEvents(context, _SAPIHandler)
        self._sapi_events._detector = self

        self.available = True
        logger.info("SAPI wake detector initialised")

    def process_audio(self, chunk: bytes) -> bool:  # noqa: ARG002
        if not self.available:
            return False
        try:
            # SAPI recognition is event-driven; this is a polling check.
            # The _SAPIHandler sets _wake_flag when a phrase is detected.
            import pythoncom  # type: ignore[import]
            pythoncom.PumpWaitingMessages()
        except Exception:  # noqa: BLE001
            pass
        if self._wake_flag:
            self._wake_flag = False
            return True
        return False

    def close(self) -> None:
        try:
            import pythoncom  # type: ignore[import]
            pythoncom.CoUninitialize()
        except Exception:  # noqa: BLE001
            pass


class _SAPIHandler:
    """COM event sink for SAPI recognition events."""

    _detector: "KeywordWakeDetector | None" = None

    def OnRecognition(self, _stream_number, _stream_position, _recognition_type, result):
        try:
            text = result.PhraseInfo.GetText()
            if _matches_wake(text):
                logger.info("Wake phrase detected by SAPI: %r", text)
                if self._detector is not None:
                    self._detector._wake_flag = True
        except Exception:  # noqa: BLE001
            pass


def build_wake_detector() -> WakeDetector:
    """
    Factory: try KeywordWakeDetector first; fall back to NullWakeDetector.

    Always returns a WakeDetector -- callers should check `.available` to
    decide whether to inform the user that voice wake detection is limited.
    """
    detector = KeywordWakeDetector()
    if detector.available:
        return detector
    logger.warning(
        "Local voice wake detection is unavailable. "
        "ZYRO will sleep/wake normally via text commands. "
        "To enable voice wake, install a supported wake-word engine."
    )
    return NullWakeDetector()


def text_is_wake_phrase(text: str) -> bool:
    """Check whether a piece of text (typed or transcribed) is a wake phrase."""
    return _matches_wake(text)


def text_is_sleep_phrase(text: str) -> bool:
    """Check whether a piece of text is a sleep command."""
    lowered = text.lower().strip()
    sleep_phrases = ("sleep", "go to sleep", "zyro sleep", "sleep mode", "hey zyro sleep")
    return any(phrase in lowered for phrase in sleep_phrases)
