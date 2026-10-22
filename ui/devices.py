"""
ui/devices.py — microphone / speaker / camera selection dialog.

Uses devices/microphones.py, devices/speakers.py, and devices/cameras.py.
Applying a selection updates devices.state.DeviceState, which the live
microphone stream and AudioPlayer already read. Camera stays OFF.
"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from audio.microphone import test_microphone
from audio.playback import AudioPlayer
from config import persist_env_values
from devices.cameras import enumerate_cameras
from devices.microphones import enumerate_microphones
from devices.speakers import enumerate_speakers
from devices.state import SYSTEM_DEFAULT_LABEL

BG = "#F3F5F8"


def _combo_values(names: list[str], empty: str) -> list[str]:
    if not names:
        return [SYSTEM_DEFAULT_LABEL, empty]
    return [SYSTEM_DEFAULT_LABEL, *names]


def open_devices_window(parent, agent, on_applied=None) -> tk.Toplevel:
    win = tk.Toplevel(parent)
    win.title("Devices")
    win.geometry("440x520")
    win.configure(bg=BG)
    win.transient(parent)
    win.grab_set()

    mic_var = tk.StringVar()
    spk_var = tk.StringVar()
    cam_var = tk.StringVar()
    hint_var = tk.StringVar(value="")

    ttk.Label(win, text="Devices", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=20, pady=(16, 4))
    ttk.Label(win, text="Camera stays OFF until you explicitly enable it later.", foreground="#6B7280").pack(
        anchor="w", padx=20, pady=(0, 12)
    )

    def _labeled_combo(title: str, var: tk.StringVar) -> ttk.Combobox:
        ttk.Label(win, text=title, font=("Segoe UI Semibold", 10)).pack(anchor="w", padx=20, pady=(10, 4))
        box = ttk.Combobox(win, textvariable=var, state="readonly")
        box.pack(fill="x", padx=20)
        return box

    mic_box = _labeled_combo("MICROPHONE", mic_var)
    spk_box = _labeled_combo("SPEAKER / OUTPUT", spk_var)
    cam_box = _labeled_combo("CAMERA", cam_var)
    ttk.Label(win, textvariable=hint_var, foreground="#6B7280", wraplength=400).pack(anchor="w", padx=20, pady=8)

    def refresh() -> dict:
        mics = enumerate_microphones()
        spks = enumerate_speakers()
        cams = enumerate_cameras()
        mic_names = [m.name for m in mics]
        spk_names = [s.name for s in spks]
        cam_names = [c.name for c in cams]
        mic_box["values"] = _combo_values(mic_names, "(no microphones detected)")
        spk_box["values"] = _combo_values(spk_names, "(no speakers detected)")
        cam_box["values"] = [SYSTEM_DEFAULT_LABEL, *(cam_names or ["No camera detected"])]

        ds = agent.device_state
        mic_var.set(ds.mic_name if ds.mic_name in mic_box["values"] else SYSTEM_DEFAULT_LABEL)
        spk_var.set(ds.speaker_name if ds.speaker_name in spk_box["values"] else SYSTEM_DEFAULT_LABEL)
        if ds.camera_name and ds.camera_name in cam_box["values"]:
            cam_var.set(ds.camera_name)
        else:
            cam_var.set("No camera detected" if not cam_names else SYSTEM_DEFAULT_LABEL)

        if not mics and not spks and not cams:
            hint_var.set("No audio or camera devices were detected.")
        elif not cams:
            hint_var.set("No camera detected. Microphone and speaker can still be used.")
        else:
            hint_var.set("")
        return {"mics": mics, "speakers": spks, "cameras": cams}

    def apply() -> bool:
        mic = mic_var.get()
        spk = spk_var.get()
        cam = cam_var.get()
        if mic.startswith("("):
            mic = SYSTEM_DEFAULT_LABEL
        if spk.startswith("("):
            spk = SYSTEM_DEFAULT_LABEL
        if cam.startswith("(") or cam == "No camera detected":
            cam = SYSTEM_DEFAULT_LABEL
        result = agent.device_state.apply(
            mic_name=mic,
            speaker_name=spk,
            camera_name=cam,
        )
        if not result.get("success"):
            messagebox.showerror("Devices", result.get("message") or "Could not apply devices.", parent=win)
            return False
        persist_env_values({
            "ZYRO_DEFAULT_MIC": "" if agent.device_state.mic_name == SYSTEM_DEFAULT_LABEL else agent.device_state.mic_name,
            "ZYRO_DEFAULT_SPEAKER": "" if agent.device_state.speaker_name == SYSTEM_DEFAULT_LABEL else agent.device_state.speaker_name,
            "ZYRO_DEFAULT_CAMERA": agent.device_state.camera_name or "",
        })
        if on_applied:
            on_applied()
        return True

    def apply_and_close() -> None:
        if apply():
            win.destroy()

    def _test_mic() -> None:
        name = mic_var.get()
        idx = None
        for mic in enumerate_microphones():
            if mic.name == name:
                idx = mic.index
                break

        def _run() -> None:
            result = test_microphone(idx)
            win.after(0, lambda: messagebox.showinfo("Test Microphone", result["message"], parent=win)
                      if result.get("success") else messagebox.showerror("Test Microphone", result["message"], parent=win))

        threading.Thread(target=_run, daemon=True).start()

    def _test_spk() -> None:
        name = spk_var.get()
        idx = None
        for spk in enumerate_speakers():
            if spk.name == name:
                idx = spk.index
                break

        def _run() -> None:
            player = AudioPlayer(device_index=idx)
            try:
                result = player.play_test_tone()
            finally:
                player.close()
            win.after(0, lambda: messagebox.showinfo("Test Speaker", result["message"], parent=win)
                      if result.get("success") else messagebox.showerror("Test Speaker", result["message"], parent=win))

        threading.Thread(target=_run, daemon=True).start()

    btns = ttk.Frame(win)
    btns.pack(fill="x", padx=20, pady=(8, 6))
    ttk.Button(btns, text="Refresh Devices", command=refresh).pack(side="left")
    ttk.Button(btns, text="Test Microphone", command=_test_mic).pack(side="left", padx=6)
    ttk.Button(btns, text="Test Speaker", command=_test_spk).pack(side="left")

    footer = ttk.Frame(win)
    footer.pack(fill="x", padx=20, pady=(16, 20), side="bottom")
    ttk.Button(footer, text="Cancel", command=win.destroy).pack(side="right")
    ttk.Button(footer, text="Apply", command=apply_and_close).pack(side="right", padx=8)

    refresh()
    return win
