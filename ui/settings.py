"""
ui/settings.py — Comprehensive interactive configuration center for ZYRO.
Allows configuring Gemini API key, model, mock mode, identity, search roots,
and testing the Gemini API key live.
"""
from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from config import persist_env_values
from ui.theme import THEME

logger = logging.getLogger("zyro.ui.settings")


def test_gemini_api_key(api_key: str, model_name: str = "gemini-2.5-flash") -> tuple[bool, str]:
    """Test whether the provided Gemini API key is valid by querying Google GenAI."""
    if not api_key.strip():
        return False, "API Key is empty."
    try:
        from google import genai
        client = genai.Client(api_key=api_key.strip())
        # Try a minimal generation call
        response = client.models.generate_content(
            model=model_name,
            contents="Say 'OK'",
        )
        if response and response.text:
            return True, f"Success! Model responded: {response.text.strip()[:30]}"
        return True, "API Key is valid!"
    except Exception as exc:
        return False, f"Connection failed: {str(exc)}"


def open_settings_window(parent, agent) -> None:
    win = tk.Toplevel(parent)
    win.title("ZYRO Settings & Configuration")
    win.geometry("560x620")
    win.minsize(500, 560)
    win.configure(bg=THEME["bg_dark"])
    win.transient(parent)

    # Style definitions
    style = ttk.Style(win)
    style.configure("Settings.TNotebook", background=THEME["bg_dark"])
    style.configure("Settings.TNotebook.Tab", padding=(12, 6), font=("Segoe UI", 10))

    # Header
    hdr = tk.Frame(win, bg=THEME["bg_dark"])
    hdr.pack(fill="x", padx=20, pady=(16, 8))
    tk.Label(
        hdr,
        text="ZYRO Configuration",
        font=("Segoe UI", 16, "bold"),
        fg=THEME["text_primary"],
        bg=THEME["bg_dark"],
    ).pack(anchor="w")
    tk.Label(
        hdr,
        text="Manage your Gemini API, identity, voice devices, and desktop integration.",
        font=("Segoe UI", 9),
        fg=THEME["text_secondary"],
        bg=THEME["bg_dark"],
    ).pack(anchor="w", pady=(2, 0))

    # Notebook tabs
    notebook = ttk.Notebook(win, style="Settings.TNotebook")
    notebook.pack(fill="both", expand=True, padx=20, pady=(8, 12))

    # Tab 1: Gemini API & Model
    tab_api = tk.Frame(notebook, bg=THEME["bg_card"], padx=18, pady=16)
    notebook.add(tab_api, text="  Gemini API  ")

    tk.Label(
        tab_api,
        text="Gemini API Key",
        font=("Segoe UI Semibold", 10),
        fg=THEME["text_primary"],
        bg=THEME["bg_card"],
    ).grid(row=0, column=0, sticky="w", pady=(0, 4))

    api_key_frame = tk.Frame(tab_api, bg=THEME["bg_card"])
    api_key_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

    api_var = tk.StringVar(value=agent.config.gemini_api_key or "")
    show_key_var = tk.BooleanVar(value=False)

    api_entry = tk.Entry(
        api_key_frame,
        textvariable=api_var,
        show="*",
        font=("Consolas", 10),
        bg=THEME["bg_input"],
        fg=THEME["text_primary"],
        insertbackground=THEME["text_primary"],
        relief="flat",
        bd=1,
        highlightthickness=1,
        highlightbackground=THEME["border"],
        highlightcolor=THEME["emerald"],
    )
    api_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 6))

    def _toggle_key_vis():
        api_entry.configure(show="" if show_key_var.get() else "*")

    show_chk = tk.Checkbutton(
        api_key_frame,
        text="Show",
        variable=show_key_var,
        command=_toggle_key_vis,
        bg=THEME["bg_card"],
        fg=THEME["text_secondary"],
        selectcolor=THEME["bg_input"],
        activebackground=THEME["bg_card"],
        activeforeground=THEME["text_primary"],
    )
    show_chk.pack(side="right")

    test_status_var = tk.StringVar(value="Click 'Test Connection' to verify API key.")
    test_lbl = tk.Label(
        tab_api,
        textvariable=test_status_var,
        font=("Segoe UI", 9, "italic"),
        fg=THEME["text_secondary"],
        bg=THEME["bg_card"],
        wraplength=480,
        justify="left",
    )
    test_lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 8))

    def _on_test_key():
        key = api_var.get().strip()
        if not key:
            test_status_var.set("Please enter an API key first.")
            test_lbl.configure(fg=THEME["rose"])
            return
        test_status_var.set("Testing connection to Gemini API...")
        test_lbl.configure(fg=THEME["amber"])

        def _test_bg():
            ok, msg = test_gemini_api_key(key, model_var.get().strip())
            if win.winfo_exists():
                win.after(0, lambda: _show_test_result(ok, msg))

        def _show_test_result(ok: bool, msg: str):
            test_status_var.set(msg)
            test_lbl.configure(fg=THEME["emerald"] if ok else THEME["rose"])

        threading.Thread(target=_test_bg, daemon=True).start()

    test_btn = tk.Button(
        tab_api,
        text="⚡ Test Connection",
        font=("Segoe UI Semibold", 9),
        bg=THEME["bg_input"],
        fg=THEME["cyan"],
        activebackground=THEME["border"],
        activeforeground=THEME["text_primary"],
        relief="flat",
        padx=12,
        pady=4,
        command=_on_test_key,
    )
    test_btn.grid(row=3, column=0, sticky="w", pady=(0, 16))

    # Model Selection
    tk.Label(
        tab_api,
        text="Gemini Model",
        font=("Segoe UI Semibold", 10),
        fg=THEME["text_primary"],
        bg=THEME["bg_card"],
    ).grid(row=4, column=0, sticky="w", pady=(0, 4))

    model_var = tk.StringVar(value=agent.config.gemini_model or "gemini-3.8-live")
    models = [
        "gemini-3.8-live",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    model_combo = ttk.Combobox(
        tab_api,
        textvariable=model_var,
        values=models,
        state="readonly",
        font=("Segoe UI", 10),
    )
    model_combo.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 16))

    # Mock Mode
    mock_var = tk.BooleanVar(value=bool(agent.config.mock_mode))
    mock_chk = tk.Checkbutton(
        tab_api,
        text="Mock Mode (Safe development -- simulated actions, no live system modification)",
        variable=mock_var,
        font=("Segoe UI", 9),
        bg=THEME["bg_card"],
        fg=THEME["text_primary"],
        selectcolor=THEME["bg_input"],
        activebackground=THEME["bg_card"],
        activeforeground=THEME["text_primary"],
    )
    mock_chk.grid(row=6, column=0, columnspan=2, sticky="w", pady=(4, 8))

    # Tab 2: Identity & Persona
    tab_persona = tk.Frame(notebook, bg=THEME["bg_card"], padx=18, pady=16)
    notebook.add(tab_persona, text="  Identity  ")

    name_var = tk.StringVar(value=agent.config.zyro_name or "ZYRO")
    user_name_var = tk.StringVar(value=agent.config.user_name or "")
    pref_name_var = tk.StringVar(value=agent.config.user_preferred_name or "")
    purpose_var = tk.StringVar(value=agent.config.zyro_purpose or "Windows-first personal AI assistant")

    persona_fields = [
        ("Agent Name", name_var),
        ("User Name", user_name_var),
        ("User Preferred Greeting Name", pref_name_var),
        ("Agent Purpose / Persona", purpose_var),
    ]

    for idx, (label_text, var) in enumerate(persona_fields):
        tk.Label(
            tab_persona,
            text=label_text,
            font=("Segoe UI Semibold", 10),
            fg=THEME["text_primary"],
            bg=THEME["bg_card"],
        ).grid(row=idx * 2, column=0, sticky="w", pady=(0, 4))

        ent = tk.Entry(
            tab_persona,
            textvariable=var,
            font=("Segoe UI", 10),
            bg=THEME["bg_input"],
            fg=THEME["text_primary"],
            insertbackground=THEME["text_primary"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=THEME["border"],
            highlightcolor=THEME["emerald"],
        )
        ent.grid(row=idx * 2 + 1, column=0, sticky="ew", pady=(0, 12))

    tab_persona.grid_columnconfigure(0, weight=1)

    # Tab 3: Search Folders
    tab_folders = tk.Frame(notebook, bg=THEME["bg_card"], padx=18, pady=16)
    notebook.add(tab_folders, text="  Search Roots  ")

    tk.Label(
        tab_folders,
        text="Folders indexed for desktop file search commands:",
        font=("Segoe UI", 9),
        fg=THEME["text_secondary"],
        bg=THEME["bg_card"],
    ).pack(anchor="w", pady=(0, 8))

    folder_listbox = tk.Listbox(
        tab_folders,
        font=("Segoe UI", 9),
        bg=THEME["bg_input"],
        fg=THEME["text_primary"],
        selectbackground=THEME["border"],
        selectforeground=THEME["text_primary"],
        relief="flat",
        bd=0,
        height=9,
    )
    folder_listbox.pack(fill="both", expand=True, pady=(0, 8))

    for p in agent.config.search_roots:
        folder_listbox.insert(tk.END, str(p))

    btn_row = tk.Frame(tab_folders, bg=THEME["bg_card"])
    btn_row.pack(fill="x")

    def _add_folder():
        chosen = filedialog.askdirectory(parent=win, title="Select Search Root Folder")
        if chosen and chosen not in folder_listbox.get(0, tk.END):
            folder_listbox.insert(tk.END, chosen)

    def _remove_folder():
        sel = folder_listbox.curselection()
        if sel:
            folder_listbox.delete(sel[0])

    tk.Button(
        btn_row,
        text="＋ Add Folder",
        font=("Segoe UI", 9),
        bg=THEME["bg_input"],
        fg=THEME["text_primary"],
        relief="flat",
        padx=10,
        pady=3,
        command=_add_folder,
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        btn_row,
        text="✕ Remove Selected",
        font=("Segoe UI", 9),
        bg=THEME["bg_input"],
        fg=THEME["rose"],
        relief="flat",
        padx=10,
        pady=3,
        command=_remove_folder,
    ).pack(side="left")

    # Bottom Actions Bar
    bottom = tk.Frame(win, bg=THEME["bg_dark"])
    bottom.pack(fill="x", padx=20, pady=(4, 16))

    def _on_save():
        new_key = api_var.get().strip()
        new_model = model_var.get().strip()
        new_mock = "true" if mock_var.get() else "false"
        new_name = name_var.get().strip() or "ZYRO"
        new_user = user_name_var.get().strip()
        new_pref = pref_name_var.get().strip()
        new_purpose = purpose_var.get().strip()
        folders = list(folder_listbox.get(0, tk.END))
        extra_folders = ",".join(folders)

        updates = {
            "GEMINI_API_KEY": new_key,
            "GEMINI_MODEL": new_model,
            "ZYRO_MOCK_MODE": new_mock,
            "ZYRO_NAME": new_name,
            "ZYRO_USER_NAME": new_user,
            "ZYRO_USER_PREFERRED_NAME": new_pref,
            "ZYRO_PURPOSE": new_purpose,
            "ZYRO_EXTRA_SEARCH_ROOTS": extra_folders,
        }

        try:
            persist_env_values(updates)
            # Update live agent config attributes
            try:
                object.__setattr__(agent.config, "gemini_api_key", new_key)
                object.__setattr__(agent.config, "gemini_model", new_model)
                object.__setattr__(agent.config, "mock_mode", mock_var.get())
                object.__setattr__(agent.config, "zyro_name", new_name)
                object.__setattr__(agent.config, "user_name", new_user)
                object.__setattr__(agent.config, "user_preferred_name", new_pref)
                object.__setattr__(agent.config, "zyro_purpose", new_purpose)
                object.__setattr__(agent.config, "search_roots", tuple(Path(f) for f in folders))
            except Exception:
                pass
            messagebox.showinfo("Settings Saved", "Settings successfully saved to .env and applied!", parent=win)
            win.destroy()
        except Exception as exc:
            messagebox.showerror("Save Error", f"Could not save settings: {exc}", parent=win)

    save_btn = tk.Button(
        bottom,
        text="💾 Save & Apply",
        font=("Segoe UI Semibold", 10),
        bg=THEME["emerald"],
        fg="#0B1120",
        activebackground=THEME["emerald_glow"],
        activeforeground="#FFFFFF",
        relief="flat",
        padx=18,
        pady=6,
        command=_on_save,
    )
    save_btn.pack(side="right")

    cancel_btn = tk.Button(
        bottom,
        text="Cancel",
        font=("Segoe UI", 10),
        bg=THEME["bg_card"],
        fg=THEME["text_secondary"],
        relief="flat",
        padx=14,
        pady=6,
        command=win.destroy,
    )
    cancel_btn.pack(side="right", padx=(0, 10))
