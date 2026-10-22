import argparse
import asyncio
from types import SimpleNamespace

import pytest

from gemini.live_client import STARTUP_GREETING, LiveClient
from tests.test_dispatcher import make_dispatcher


def test_startup_greeting_text():
    assert STARTUP_GREETING == "Hello sir, how can I help you?"


def test_default_cli_mode_is_app():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["app", "status", "voice", "text", "ui"], default="app")
    assert parser.parse_args([]).mode == "app"
    assert parser.parse_args(["--mode", "text"]).mode == "text"
    assert parser.parse_args(["--mode", "voice"]).mode == "voice"
    assert parser.parse_args(["--mode", "ui"]).mode == "ui"


class _FakeSession:
    def __init__(self, turns):
        self._turns = [list(turn) for turn in turns]
        self.tool_responses = 0

    async def receive(self):
        if not self._turns:
            await asyncio.Future()
            return
            yield
        for message in self._turns.pop(0):
            yield message

    async def send_tool_response(self, function_responses=None):
        self.tool_responses += 1


def _msg(*, tool_call=None, turn_complete=False, output=None):
    content = None
    if turn_complete or output:
        content = SimpleNamespace(
            input_transcription=None,
            output_transcription=SimpleNamespace(text=output) if output else None,
            model_turn=None,
            turn_complete=turn_complete,
        )
    return SimpleNamespace(tool_call=tool_call, server_content=content)


@pytest.mark.asyncio
async def test_receive_loop_plays_audio_and_shows_text():
    dispatcher = make_dispatcher()
    client = LiveClient(SimpleNamespace(), dispatcher)
    audio = []
    texts = []
    part = SimpleNamespace(inline_data=SimpleNamespace(data=b"pcm"))
    content = SimpleNamespace(
        input_transcription=None,
        output_transcription=SimpleNamespace(text="2 + 2 is 4."),
        model_turn=SimpleNamespace(parts=[part]),
        turn_complete=True,
    )
    session = _FakeSession([[SimpleNamespace(tool_call=None, server_content=content)]])
    task = asyncio.create_task(
        client._receive_loop(session, on_audio_out=audio.append, on_text_out=texts.append)
    )
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert b"pcm" in audio
    assert "2 + 2 is 4." in texts


@pytest.mark.asyncio
async def test_submit_text_uses_live_queue():
    dispatcher = make_dispatcher()
    client = LiveClient(SimpleNamespace(), dispatcher)
    client._loop = asyncio.get_running_loop()
    client._text_queue = asyncio.Queue()
    assert client.submit_text("What is 2 + 2?") is True
    await asyncio.sleep(0)
    assert await client._text_queue.get() == "What is 2 + 2?"
    assert client._suppress_mic is True


def test_submit_text_without_session_returns_false():
    client = LiveClient(SimpleNamespace(), make_dispatcher())
    assert client.submit_text("hello") is False


@pytest.mark.asyncio
async def test_mixed_text_after_tool_call():
    dispatcher = make_dispatcher()
    client = LiveClient(SimpleNamespace(), dispatcher)
    tool_call = SimpleNamespace(
        function_calls=[SimpleNamespace(name="safe_echo", args={"text": "hi"}, id="fc1")]
    )
    tools = []
    texts = []
    users = []
    session = _FakeSession(
        [
            [_msg(tool_call=tool_call), _msg(turn_complete=True)],
            [_msg(output="4", turn_complete=True)],
            [_msg(output="Notepad is open.", turn_complete=True)],
        ]
    )
    task = asyncio.create_task(
        client._receive_loop(
            session,
            on_text_out=texts.append,
            on_user_text=users.append,
            on_tool=lambda name, args: tools.append(name),
        )
    )
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert session.tool_responses == 1
    assert tools == ["safe_echo"]
    assert "4" in texts
    assert "Notepad is open." in texts


@pytest.mark.asyncio
async def test_receive_loop_continues_after_tool_call():
    dispatcher = make_dispatcher()
    client = LiveClient(SimpleNamespace(), dispatcher)
    tool_call = SimpleNamespace(
        function_calls=[SimpleNamespace(name="safe_echo", args={"text": "hi"}, id="fc1")]
    )
    texts = []
    session = _FakeSession(
        [
            [_msg(tool_call=tool_call), _msg(turn_complete=True)],
            [_msg(output="four", turn_complete=False), _msg(turn_complete=True)],
        ]
    )

    task = asyncio.create_task(client._receive_loop(session, on_text_out=texts.append))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert session.tool_responses == 1
    assert "four" in texts
