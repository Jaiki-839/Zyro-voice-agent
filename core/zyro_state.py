"""
core/zyro_state.py -- Centralized sleep/wake state machine for ZYRO.

States:
  STARTING  -- application is initialising
  ACTIVE    -- normal operation; all tools run, mic -> Gemini
  SLEEPING  -- sleep mode; mic NOT sent to Gemini; only local wake detection
  STOPPING  -- graceful shutdown in progress

Rules:
  - Thread-safe: all mutations use a lock.
  - Never persisted to disk (starts ACTIVE after every restart).
  - Only StateManager mutates state; no scattered booleans elsewhere.
  - On state change, registered callbacks are fired (on the calling thread).
"""
from __future__ import annotations

import logging
import threading
from enum import Enum
from typing import Callable

logger = logging.getLogger("zyro.state")


class ZyroState(str, Enum):
    STARTING = "STARTING"
    ACTIVE = "ACTIVE"
    SLEEPING = "SLEEPING"
    STOPPING = "STOPPING"


class StateManager:
    """
    Central, thread-safe state machine.

    Usage::

        mgr = StateManager()
        mgr.on_change(lambda old, new: print(f"{old} -> {new}"))
        mgr.set_sleeping()   # ACTIVE -> SLEEPING
        mgr.set_active()     # SLEEPING -> ACTIVE
    """

    def __init__(self, initial: ZyroState = ZyroState.ACTIVE) -> None:
        self._state: ZyroState = initial
        self._lock = threading.Lock()
        self._callbacks: list[Callable[[ZyroState, ZyroState], None]] = []

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @property
    def state(self) -> ZyroState:
        with self._lock:
            return self._state

    def is_sleeping(self) -> bool:
        return self.state == ZyroState.SLEEPING

    def is_active(self) -> bool:
        return self.state == ZyroState.ACTIVE

    def is_stopping(self) -> bool:
        return self.state == ZyroState.STOPPING

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------

    def set_active(self) -> None:
        self._transition(ZyroState.ACTIVE)

    def set_sleeping(self) -> None:
        self._transition(ZyroState.SLEEPING)

    def set_stopping(self) -> None:
        self._transition(ZyroState.STOPPING)

    def set_starting(self) -> None:
        self._transition(ZyroState.STARTING)

    def _transition(self, new_state: ZyroState) -> None:
        with self._lock:
            old_state = self._state
            if old_state == new_state:
                logger.debug("StateManager: already in %s, ignoring transition", new_state)
                return
            self._state = new_state
            callbacks = list(self._callbacks)

        logger.info("ZYRO state: %s -> %s", old_state, new_state)
        for cb in callbacks:
            try:
                cb(old_state, new_state)
            except Exception:  # noqa: BLE001
                logger.exception("StateManager callback raised an exception")

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def on_change(self, callback: Callable[[ZyroState, ZyroState], None]) -> None:
        """Register a callback fired on every state transition.

        Callback receives (old_state, new_state).  Called on the thread that
        triggered the transition -- UI callbacks must marshal to the main thread
        themselves (e.g. via root.after()).
        """
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ZyroState, ZyroState], None]) -> None:
        with self._lock:
            try:
                self._callbacks.remove(callback)
            except ValueError:
                pass

    def __repr__(self) -> str:
        return f"StateManager(state={self._state})"
