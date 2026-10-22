from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from devices.state import SYSTEM_DEFAULT_LABEL, DeviceState
from ui.chat import ConversationView
from ui.main_window import ZyroMainWindow, _tool_status_line


def _fake_agent() -> MagicMock:
    agent = MagicMock()
    agent.config.zyro_name = "ZYRO"
    agent.config.mock_mode = True
    agent.config.gemini_model = "gemini-3.8-live"
    agent.config.log_level = "INFO"
    agent.config.search_roots = ()
    agent.device_state = DeviceState()
    agent.live_client.submit_text = MagicMock(return_value=True)
    return agent


@pytest.fixture
def window():
    win = ZyroMainWindow(_fake_agent(), start_voice=False)
    win.root.withdraw()
    win.root.update_idletasks()
    yield win
    win.root.destroy()


def test_ui_starts(window):
    assert window.entry.winfo_exists()
    assert window.send_btn.winfo_exists()
    assert window.status_var.get() == "Idle"


def test_text_message_is_sent(window):
    assert window.send_message("What is 2 + 2?") is True
    window.agent.live_client.submit_text.assert_called_once_with("What is 2 + 2?")
    text = window.chat.get_text()
    assert "YOU" in text
    assert "What is 2 + 2?" in text


def test_text_response_is_displayed(window):
    window._on_assistant("2 + 2 is 4.")
    window.root.update()
    assert "2 + 2 is 4." in window.chat.get_text()
    assert "ZYRO" in window.chat.get_text()


def test_voice_input_still_renders(window):
    window._on_user_voice("Open Chrome.")
    window.root.update()
    assert "Open Chrome." in window.chat.get_text()
    assert "YOU" in window.chat.get_text()


def test_tool_status_is_human_readable():
    assert "Chrome" in _tool_status_line("open_application", {"name": "Chrome"})


def test_conversation_auto_scrolls(window):
    view: ConversationView = window.chat
    window.send_message("hello")
    window._on_assistant("hi there")
    window.root.update()
    # Tk reports the end index after the last character we inserted.
    assert float(view.widget.index("end-1c").split(".")[0]) >= 2


def test_send_does_nothing_when_disconnected():
    agent = _fake_agent()
    agent.live_client.submit_text = MagicMock(return_value=False)
    try:
        win = ZyroMainWindow(agent, start_voice=False)
    except tk.TclError as exc:
        pytest.skip(f"Tk is not usable in this environment: {exc}")
    win.root.withdraw()
    try:
        assert win.send_message("hello") is False
        assert "YOU" not in win.chat.get_text()
    finally:
        win.root.destroy()
