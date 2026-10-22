from types import SimpleNamespace
from unittest.mock import MagicMock

from audio.playback import AudioPlayer
from config import persist_env_values
from devices.state import SYSTEM_DEFAULT_LABEL, DeviceState
from ui.devices import _combo_values, open_devices_window
from ui.main_window import ZyroMainWindow


def test_device_refresh_builds_dropdown_values():
    values = _combo_values(["USB Mic", "Headset"], "(no microphones detected)")
    assert values[0] == SYSTEM_DEFAULT_LABEL
    assert "USB Mic" in values


def test_device_refresh_handles_empty_lists():
    values = _combo_values([], "(no microphones detected)")
    assert SYSTEM_DEFAULT_LABEL in values
    assert "(no microphones detected)" in values


def test_selected_microphone_is_applied(monkeypatch):
    mic = SimpleNamespace(index=4, name="USB Mic")
    monkeypatch.setattr("devices.state.find_microphone", lambda name: mic if "USB" in name else None)
    state = DeviceState()
    source = MagicMock()
    state.mic_source = source
    result = state.apply(mic_name="USB Mic")
    assert result["success"] is True
    assert state.mic_index == 4
    assert state.mic_name == "USB Mic"
    source.set_device.assert_called_once_with(4)


def test_selected_speaker_is_applied(monkeypatch):
    spk = SimpleNamespace(index=7, name="Headphones")
    monkeypatch.setattr("devices.state.find_speaker", lambda name: spk if "Head" in name else None)
    state = DeviceState()
    player = MagicMock()
    state.player = player
    result = state.apply(speaker_name="Headphones")
    assert result["success"] is True
    assert state.speaker_index == 7
    player.set_device.assert_called_once_with(7)


def test_selected_camera_is_applied_but_stays_off(monkeypatch):
    cam = SimpleNamespace(index=1, name="Camera 1")
    monkeypatch.setattr("devices.state.find_camera", lambda name: cam if "Camera" in name else None)
    state = DeviceState()
    result = state.apply(camera_name="Camera 1")
    assert result["success"] is True
    assert state.camera_index == 1
    assert state.camera_name == "Camera 1"
    assert state.camera_enabled is False


def test_audio_player_set_device_does_not_need_a_stream():
    player = AudioPlayer()
    player.set_device(2)
    assert player._device_index == 2
    player.set_device(None)
    assert player._device_index is None


def test_devices_dialog_refresh(monkeypatch):
    monkeypatch.setattr("ui.devices.enumerate_microphones", lambda: [SimpleNamespace(name="Mic A", index=0)])
    monkeypatch.setattr("ui.devices.enumerate_speakers", lambda: [SimpleNamespace(name="Spk A", index=1)])
    monkeypatch.setattr("ui.devices.enumerate_cameras", lambda: [])
    agent = MagicMock()
    agent.config.zyro_name = "ZYRO"
    agent.config.mock_mode = True
    agent.device_state = DeviceState()
    agent.live_client.submit_text = MagicMock(return_value=False)
    try:
        parent = ZyroMainWindow(agent, start_voice=False)
    except Exception as exc:
        import tkinter as tk
        if isinstance(exc, tk.TclError):
            pytest.skip(f"Tk is not usable in this environment: {exc}")
        raise
    parent.root.withdraw()
    try:
        dialog = open_devices_window(parent.root, agent)
        dialog.update_idletasks()
        # values include default + detected mic
        kids = [w for w in dialog.winfo_children()]
        assert kids
        dialog.destroy()
    finally:
        parent.root.destroy()


def test_persist_device_keys_only(tmp_path):
    env = tmp_path / ".env"
    env.write_text("GEMINI_API_KEY=secret\nZYRO_NAME=ZYRO\n", encoding="utf-8")
    persist_env_values({"ZYRO_DEFAULT_MIC": "USB Mic"}, env_path=env)
    text = env.read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=secret" in text
    assert "ZYRO_DEFAULT_MIC=USB Mic" in text
    assert "ZYRO_NAME=ZYRO" in text
