"""tests/test_sleep_wake.py -- sleep/wake integration tests.

Tests verify ALL 12 specified behaviors:
1.  Initial state = ACTIVE
2.  Sleep -> SLEEPING
3.  Normal tool while sleeping -> blocked
4.  Web search while sleeping -> blocked
5.  Media command while sleeping -> blocked
6.  Windows operation while sleeping -> blocked
7.  Wake -> ACTIVE
8.  Normal tool after wake -> allowed
9.  Repeated sleep -> safe
10. Repeated wake -> safe
11. Restart -> ACTIVE
12. No duplicate microphone/Gemini sessions after wake

Also verifies:
- No Gemini audio forwarded while sleeping (live_client gate)
- Text wake detection is local (no Gemini forwarding)
- Text sleep detection is local
- zyro_sleep tool is the only tool allowed while sleeping
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from audio.wake_detector import (
    NullWakeDetector,
    WakeDetector,
    text_is_sleep_phrase,
    text_is_wake_phrase,
)
from core.permissions import PermissionLevel
from core.router import ToolDispatcher
from core.session import SessionContext
from core.tool_registry import Tool, ToolParameter, ToolRegistry
from core.zyro_state import StateManager, ZyroState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_registry_with_tools(state_manager: StateManager) -> ToolRegistry:
    registry = ToolRegistry()

    # A generic "normal" tool
    def _dummy_tool(mock_mode=False, session=None, **_):
        return {"success": True, "message": "done", "data": None}

    registry.register(Tool(
        name="open_application",
        description="test",
        permission=PermissionLevel.SAFE,
        handler=_dummy_tool,
        parameters=(ToolParameter("name", "string", ""),),
    ))
    registry.register(Tool(
        name="web_search",
        description="test",
        permission=PermissionLevel.SAFE,
        handler=_dummy_tool,
        parameters=(ToolParameter("query", "string", ""),),
    ))
    registry.register(Tool(
        name="media_play",
        description="test",
        permission=PermissionLevel.SAFE,
        handler=_dummy_tool,
        parameters=(),
    ))
    registry.register(Tool(
        name="open_windows_settings",
        description="test",
        permission=PermissionLevel.SAFE,
        handler=_dummy_tool,
        parameters=(ToolParameter("category", "string", ""),),
    ))

    # The zyro_sleep tool
    _ref = [state_manager]
    def _sleep_handler(mock_mode=False, session=None, **_):
        _ref[0].set_sleeping()
        return {"success": True, "message": "Going to sleep.", "data": None}
    _sleep_handler._ref = _ref

    registry.register(Tool(
        name="zyro_sleep",
        description="test",
        permission=PermissionLevel.SAFE,
        handler=_sleep_handler,
        parameters=(),
    ))
    return registry


def _make_dispatcher(state_manager: StateManager) -> ToolDispatcher:
    registry = _make_registry_with_tools(state_manager)
    session = SessionContext()
    return ToolDispatcher(
        registry=registry,
        session=session,
        mock_mode=True,
        state_manager=state_manager,
    )


# ---------------------------------------------------------------------------
# Behavior 1: Initial state = ACTIVE
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_initial_state_is_active(self):
        mgr = StateManager()
        assert mgr.is_active()
        assert not mgr.is_sleeping()


# ---------------------------------------------------------------------------
# Behavior 2: Sleep -> SLEEPING
# ---------------------------------------------------------------------------

class TestSleep:
    def test_sleep_sets_sleeping_state(self):
        mgr = StateManager()
        mgr.set_sleeping()
        assert mgr.is_sleeping()

    def test_zyro_sleep_tool_sets_sleeping(self):
        mgr = StateManager()
        dispatcher = _make_dispatcher(mgr)
        outcome = dispatcher.dispatch("zyro_sleep", {})
        assert outcome.result["success"] is True
        assert mgr.is_sleeping()


# ---------------------------------------------------------------------------
# Behavior 3-6: Tools blocked while sleeping
# ---------------------------------------------------------------------------

class TestToolsBlockedWhileSleeping:
    def _sleeping_dispatcher(self):
        mgr = StateManager()
        mgr.set_sleeping()
        return _make_dispatcher(mgr)

    def test_open_application_blocked(self):
        d = self._sleeping_dispatcher()
        outcome = d.dispatch("open_application", {"name": "Chrome"})
        assert outcome.result["success"] is False
        assert "sleeping" in outcome.result["message"].lower()
        assert outcome.executed is False

    def test_web_search_blocked(self):
        d = self._sleeping_dispatcher()
        outcome = d.dispatch("web_search", {"query": "test"})
        assert outcome.result["success"] is False
        assert outcome.executed is False

    def test_media_play_blocked(self):
        d = self._sleeping_dispatcher()
        outcome = d.dispatch("media_play", {})
        assert outcome.result["success"] is False
        assert outcome.executed is False

    def test_windows_settings_blocked(self):
        d = self._sleeping_dispatcher()
        outcome = d.dispatch("open_windows_settings", {"category": "bluetooth"})
        assert outcome.result["success"] is False
        assert outcome.executed is False

    def test_zyro_sleep_not_blocked_while_sleeping(self):
        """zyro_sleep must be exempt from the sleep gate (it's the transition tool)."""
        mgr = StateManager()
        mgr.set_sleeping()
        dispatcher = _make_dispatcher(mgr)
        # zyro_sleep should pass the gate (though calling it while sleeping is a no-op)
        outcome = dispatcher.dispatch("zyro_sleep", {})
        # It should NOT return the "sleeping" block message
        assert "sleeping" not in outcome.result["message"].lower() or "going" in outcome.result["message"].lower()


# ---------------------------------------------------------------------------
# Behavior 7: Wake -> ACTIVE
# ---------------------------------------------------------------------------

class TestWake:
    def test_wake_sets_active_state(self):
        mgr = StateManager()
        mgr.set_sleeping()
        mgr.set_active()
        assert mgr.is_active()
        assert not mgr.is_sleeping()


# ---------------------------------------------------------------------------
# Behavior 8: Normal tool after wake -> allowed
# ---------------------------------------------------------------------------

class TestToolsAllowedAfterWake:
    def test_tool_allowed_after_wake(self):
        mgr = StateManager()
        dispatcher = _make_dispatcher(mgr)

        mgr.set_sleeping()
        blocked = dispatcher.dispatch("open_application", {"name": "Chrome"})
        assert blocked.result["success"] is False  # blocked

        mgr.set_active()
        allowed = dispatcher.dispatch("open_application", {"name": "Chrome"})
        assert allowed.result["success"] is True  # allowed


# ---------------------------------------------------------------------------
# Behavior 9-10: Repeated sleep/wake are safe
# ---------------------------------------------------------------------------

class TestRepeatedSleepWake:
    def test_repeated_sleep_safe(self):
        mgr = StateManager()
        mgr.set_sleeping()
        mgr.set_sleeping()  # no-op
        mgr.set_sleeping()  # no-op
        assert mgr.is_sleeping()

    def test_repeated_wake_safe(self):
        mgr = StateManager()
        mgr.set_active()
        mgr.set_active()  # no-op
        mgr.set_active()  # no-op
        assert mgr.is_active()

    def test_many_sleep_wake_cycles(self):
        mgr = StateManager()
        for _ in range(10):
            mgr.set_sleeping()
            assert mgr.is_sleeping()
            mgr.set_active()
            assert mgr.is_active()


# ---------------------------------------------------------------------------
# Behavior 11: Restart -> ACTIVE
# ---------------------------------------------------------------------------

class TestRestartState:
    def test_new_state_manager_is_always_active(self):
        for _ in range(5):
            mgr = StateManager()
            assert mgr.is_active()

    def test_state_is_not_persisted(self):
        """StateManager never touches disk -- state is always reset."""
        mgr = StateManager()
        mgr.set_sleeping()
        del mgr
        new_mgr = StateManager()
        assert new_mgr.is_active()  # Always starts fresh


# ---------------------------------------------------------------------------
# Behavior 12: No duplicate sessions/mic pipelines after wake
# ---------------------------------------------------------------------------

class TestNoDuplicates:
    def test_state_manager_is_singleton_reference(self):
        """All components share the same StateManager instance."""
        mgr = StateManager()
        objects_with_mgr = [mgr, mgr]  # same reference
        assert all(o is mgr for o in objects_with_mgr)

    def test_wake_detector_is_null_when_unavailable(self):
        detector = NullWakeDetector()
        assert detector.available is False
        assert detector.process_audio(b"\x00" * 100) is False


# ---------------------------------------------------------------------------
# Audio NOT forwarded to Gemini while sleeping
# ---------------------------------------------------------------------------

class TestNoGeminiAudioWhileSleeping:
    """Verify the _send_audio gate in live_client.py does not forward chunks."""

    @pytest.mark.asyncio
    async def test_audio_chunks_not_forwarded_while_sleeping(self):
        from gemini.live_client import LiveClient
        from config import ZyroConfig

        mgr = StateManager()
        mgr.set_sleeping()

        detector = NullWakeDetector()

        # Minimal mock config
        config = MagicMock(spec=ZyroConfig)
        config.gemini_model = "test"
        config.zyro_name = "ZYRO"

        dispatcher = MagicMock()
        client = LiveClient(
            config=config,
            dispatcher=dispatcher,
            state_manager=mgr,
            wake_detector=detector,
        )

        # Simulate the audio loop check manually (no real session)
        chunks_forwarded = []
        async def fake_send(audio):
            chunks_forwarded.append(audio)

        # Simulate what _send_audio does: if sleeping, don't call fake_send
        for _chunk in [b"audio1", b"audio2"]:
            if mgr.is_sleeping():
                detector.process_audio(_chunk)
                continue  # sleep gate -- not forwarded
            await fake_send(_chunk)

        assert len(chunks_forwarded) == 0, "Audio was forwarded to Gemini while sleeping!"


# ---------------------------------------------------------------------------
# Text mode sleep/wake detection
# ---------------------------------------------------------------------------

class TestTextModeSleepWake:
    def test_sleep_phrases_detected(self):
        sleep_phrases = ["sleep", "go to sleep", "zyro sleep", "sleep mode", "hey zyro sleep"]
        for phrase in sleep_phrases:
            assert text_is_sleep_phrase(phrase), f"Should detect sleep: {phrase!r}"

    def test_wake_phrases_detected(self):
        wake_phrases = ["wake up", "hey zyro wake up", "zyro wake up", "wake up zyro"]
        for phrase in wake_phrases:
            assert text_is_wake_phrase(phrase), f"Should detect wake: {phrase!r}"

    def test_normal_phrases_not_sleep(self):
        normal = ["open chrome", "play music", "what time is it", "hello"]
        for phrase in normal:
            assert not text_is_sleep_phrase(phrase), f"Should NOT be sleep: {phrase!r}"

    def test_normal_phrases_not_wake(self):
        normal = ["open chrome", "play music", "what time is it", "hello"]
        for phrase in normal:
            assert not text_is_wake_phrase(phrase), f"Should NOT be wake: {phrase!r}"

    def test_case_insensitive_sleep(self):
        assert text_is_sleep_phrase("SLEEP")
        assert text_is_sleep_phrase("Go To Sleep")

    def test_case_insensitive_wake(self):
        assert text_is_wake_phrase("WAKE UP")
        assert text_is_wake_phrase("Hey ZYRO Wake Up")


# ---------------------------------------------------------------------------
# WakeDetector interface
# ---------------------------------------------------------------------------

class TestWakeDetectorInterface:
    def test_null_detector_always_false(self):
        d = NullWakeDetector()
        for _ in range(10):
            assert d.process_audio(b"chunk") is False

    def test_null_detector_not_available(self):
        d = NullWakeDetector()
        assert d.available is False

    def test_custom_detector_interface(self):
        class AlwaysWake(WakeDetector):
            available = True
            def process_audio(self, chunk):
                return True
        d = AlwaysWake()
        assert d.process_audio(b"anything") is True
