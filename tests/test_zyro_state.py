"""tests/test_zyro_state.py -- unit tests for core/zyro_state.py"""
from __future__ import annotations

import threading
import time

import pytest

from core.zyro_state import StateManager, ZyroState


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

class TestInitialState:
    def test_default_initial_state_is_active(self):
        mgr = StateManager()
        assert mgr.state == ZyroState.ACTIVE

    def test_is_active_true_by_default(self):
        mgr = StateManager()
        assert mgr.is_active() is True

    def test_is_sleeping_false_by_default(self):
        mgr = StateManager()
        assert mgr.is_sleeping() is False

    def test_custom_initial_state(self):
        mgr = StateManager(initial=ZyroState.STARTING)
        assert mgr.state == ZyroState.STARTING

    def test_restart_always_starts_active(self):
        """Simulated restart: new StateManager() always starts ACTIVE."""
        mgr1 = StateManager()
        mgr1.set_sleeping()
        assert mgr1.is_sleeping()
        # New instance (simulating restart) starts fresh
        mgr2 = StateManager()
        assert mgr2.is_active()


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

class TestTransitions:
    def test_active_to_sleeping(self):
        mgr = StateManager()
        mgr.set_sleeping()
        assert mgr.is_sleeping() is True
        assert mgr.is_active() is False

    def test_sleeping_to_active(self):
        mgr = StateManager()
        mgr.set_sleeping()
        mgr.set_active()
        assert mgr.is_active() is True
        assert mgr.is_sleeping() is False

    def test_active_sleeping_active_cycle(self):
        mgr = StateManager()
        for _ in range(3):
            mgr.set_sleeping()
            assert mgr.is_sleeping()
            mgr.set_active()
            assert mgr.is_active()

    def test_repeated_sleep_is_safe(self):
        mgr = StateManager()
        mgr.set_sleeping()
        mgr.set_sleeping()  # no-op, must not raise
        assert mgr.is_sleeping()

    def test_repeated_wake_is_safe(self):
        mgr = StateManager()
        mgr.set_active()
        mgr.set_active()  # no-op, must not raise
        assert mgr.is_active()

    def test_set_stopping(self):
        mgr = StateManager()
        mgr.set_stopping()
        assert mgr.is_stopping() is True
        assert mgr.state == ZyroState.STOPPING

    def test_set_starting(self):
        mgr = StateManager()
        mgr.set_starting()
        assert mgr.state == ZyroState.STARTING


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

class TestCallbacks:
    def test_callback_fired_on_sleep(self):
        mgr = StateManager()
        events: list[tuple] = []
        mgr.on_change(lambda old, new: events.append((old, new)))
        mgr.set_sleeping()
        assert len(events) == 1
        assert events[0] == (ZyroState.ACTIVE, ZyroState.SLEEPING)

    def test_callback_fired_on_wake(self):
        mgr = StateManager()
        events: list[tuple] = []
        mgr.set_sleeping()
        mgr.on_change(lambda old, new: events.append((old, new)))
        mgr.set_active()
        assert len(events) == 1
        assert events[0] == (ZyroState.SLEEPING, ZyroState.ACTIVE)

    def test_no_callback_on_same_state(self):
        mgr = StateManager()
        events: list[tuple] = []
        mgr.on_change(lambda old, new: events.append((old, new)))
        mgr.set_active()  # already ACTIVE -> no-op
        assert len(events) == 0

    def test_multiple_callbacks(self):
        mgr = StateManager()
        a: list[int] = []
        b: list[int] = []
        mgr.on_change(lambda *_: a.append(1))
        mgr.on_change(lambda *_: b.append(1))
        mgr.set_sleeping()
        assert len(a) == 1
        assert len(b) == 1

    def test_remove_callback(self):
        mgr = StateManager()
        events: list = []
        cb = lambda old, new: events.append((old, new))  # noqa: E731
        mgr.on_change(cb)
        mgr.remove_callback(cb)
        mgr.set_sleeping()
        assert len(events) == 0

    def test_callback_exception_does_not_break_state(self):
        mgr = StateManager()
        def bad_cb(old, new):
            raise RuntimeError("callback error")
        mgr.on_change(bad_cb)
        mgr.set_sleeping()  # must not raise
        assert mgr.is_sleeping()


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_transitions_are_safe(self):
        mgr = StateManager()
        errors: list[Exception] = []

        def _flip():
            try:
                for _ in range(50):
                    mgr.set_sleeping()
                    mgr.set_active()
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=_flip) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert not errors, f"Thread errors: {errors}"
        # After all threads finish, state should be one of the valid states
        assert mgr.state in (ZyroState.ACTIVE, ZyroState.SLEEPING)

    def test_concurrent_callback_registration(self):
        mgr = StateManager()
        events: list = []

        def _register_and_sleep():
            mgr.on_change(lambda o, n: events.append(n))
            mgr.set_sleeping()
            mgr.set_active()

        threads = [threading.Thread(target=_register_and_sleep) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        # No exceptions = pass


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------

def test_repr():
    mgr = StateManager()
    r = repr(mgr)
    assert "StateManager" in r
    assert "ACTIVE" in r
