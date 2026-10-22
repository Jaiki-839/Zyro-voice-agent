"""
ui/setup_wizard.py -- Interactive First-Run Setup Wizard for ZYRO Desktop.
Provides a guided graphical setup experience for new users to configure
their Gemini API Key, audio devices, and assistant identity without needing
to edit configuration files or use command line.
"""
from __future__ import annotations

import logging
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

from config import persist_env_values
from ui.theme import THEME
from ui.settings import test_gemini_api_key

logger = logging.getLogger("zyro.ui.setup")


class ZyroSetupWizard:
    def __init__(self, on_completed=None) -> None:
        self.on_completed = on_completed
        self.root = tk.Tk()
        self.root.title("ZYRO Voice Agent -- First-Time Setup Wizard")
        self.root.geometry("620x680")
        self.root.minsize(560, 600)
        self.root.configure(bg=THEME["bg_dark"])

        # Try setting icon if available
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "zyro.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.current_step = 0
        self._build_ui()

    def _build_ui(self) -> None:
        # Header banner
        header = tk.Frame(self.root, bg=THEME["bg_card"], padx=24, pady=20)
        header.pack(fill="x")

        title_row = tk.Frame(header, bg=THEME["bg_card"])
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="⚡ ZYRO",
            font=("Segoe UI", 22, "bold"),
            fg=THEME["emerald"],
            bg=THEME["bg_card"],
        ).pack(side="left")

        tk.Label(
            title_row,
            text=" Desktop Voice Agent Setup",
            font=("Segoe UI", 16, "bold"),
            fg=THEME["text_primary"],
            bg=THEME["bg_card"],
        ).pack(side="left", padx=(4, 0), pady=(4, 0))

        tk.Label(
            header,
            text="Configure your Gemini API key, microphone, and preferences to start chatting.",
            font=("Segoe UI", 10),
            fg=THEME["text_secondary"],
            bg=THEME["bg_card"],
        ).pack(anchor="w", pady=(6, 0))

        # Main Step Container
        self.content_frame = tk.Frame(self.root, bg=THEME["bg_dark"], padx=28, pady=20)
        self.content_frame.pack(fill="both", expand=True)

        # Variables
        self.api_key_var = tk.StringVar()
        self.model_var = tk.StringVar(value="gemini-3.8-live")
        self.mock_mode_var = tk.BooleanVar(value=False)
        self.user_name_var = tk.StringVar()
        self.agent_name_var = tk.StringVar(value="ZYRO")
        self.mic_var = tk.StringVar(value="System Default")
        self.speaker_var = tk.StringVar(value="System Default")

        # Step 1: Gemini API
        self.step1_frame = tk.Frame(self.content_frame, bg=THEME["bg_dark"])
        self._build_step1(self.step1_frame)

        # Navigation Footer
        footer = tk.Frame(self.root, bg=THEME["bg_card"], padx=24, pady=16)
        footer.pack(fill="x", side="bottom")

        self.status_label = tk.Label(
            footer,
            text="Ready to configure.",
            font=("Segoe UI", 9, "italic"),
            fg=THEME["text_secondary"],
            bg=THEME["bg_card"],
        )
        self.status_label.pack(side="left")

        self.btn_finish = tk.Button(
            footer,
            text="Complete & Launch ZYRO  ➔",
            font=("Segoe UI Semibold", 10),
            bg=THEME["emerald"],
            fg="#0B1120",
            activebackground=THEME["emerald_glow"],
            activeforeground="#FFFFFF",
            relief="flat",
            padx=18,
            pady=8,
            command=self._on_finish,
        )
        self.btn_finish.pack(side="right")

        self.step1_frame.pack(fill="both", expand=True)

    def _build_step1(self, parent: tk.Frame) -> None:
        # Step 1: Gemini API Setup Card
        card = tk.Frame(parent, bg=THEME["bg_card"], padx=20, pady=18, highlightbackground=THEME["border"], highlightthickness=1)
        card.pack(fill="x", pady=(0, 16))

        tk.Label(
            card,
            text="Step 1: Connect your Gemini API Key",
            font=("Segoe UI Semibold", 12),
            fg=THEME["text_primary"],
            bg=THEME["bg_card"],
        ).pack(anchor="w")

        tk.Label(
            card,
            text="ZYRO uses Google's Gemini Live API for real-time natural voice conversation.",
            font=("Segoe UI", 9),
            fg=THEME["text_secondary"],
            bg=THEME["bg_card"],
        ).pack(anchor="w", pady=(2, 10))

        # API Key Row
        key_box = tk.Frame(card, bg=THEME["bg_card"])
        key_box.pack(fill="x", pady=(0, 8))

        self.key_entry = tk.Entry(
            key_box,
            textvariable=self.api_key_var,
            font=("Consolas", 11),
            bg=THEME["bg_input"],
            fg=THEME["text_primary"],
            insertbackground=THEME["text_primary"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=THEME["border"],
            highlightcolor=THEME["emerald"],
        )
        self.key_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))

        def _open_ai_studio():
            webbrowser.open_new("https://aistudio.google.com/app/apikey")

        get_key_btn = tk.Button(
            key_box,
            text="🔑 Get Free Key",
            font=("Segoe UI Semibold", 9),
            bg=THEME["bg_input"],
            fg=THEME["cyan"],
            relief="flat",
            padx=12,
            pady=6,
            command=_open_ai_studio,
        )
        get_key_btn.pack(side="right")

        # Test key row
        test_row = tk.Frame(card, bg=THEME["bg_card"])
        test_row.pack(fill="x", pady=(0, 6))

        self.key_status_lbl = tk.Label(
            test_row,
            text="Paste your key above, then click 'Verify Key'.",
            font=("Segoe UI", 9, "italic"),
            fg=THEME["text_secondary"],
            bg=THEME["bg_card"],
        )
        self.key_status_lbl.pack(side="left")

        def _verify_key():
            k = self.api_key_var.get().strip()
            if not k:
                self.key_status_lbl.configure(text="Please paste an API key first.", fg=THEME["rose"])
                return
            self.key_status_lbl.configure(text="Verifying API key with Google GenAI...", fg=THEME["amber"])

            def _bg():
                ok, msg = test_gemini_api_key(k)
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self._show_verify_result(ok, msg))

            threading.Thread(target=_bg, daemon=True).start()

        verify_btn = tk.Button(
            test_row,
            text="Verify Key",
            font=("Segoe UI", 9),
            bg=THEME["border"],
            fg=THEME["text_primary"],
            relief="flat",
            padx=10,
            pady=3,
            command=_verify_key,
        )
        verify_btn.pack(side="right")

        # Step 2: Personalization & Preferences
        card2 = tk.Frame(parent, bg=THEME["bg_card"], padx=20, pady=18, highlightbackground=THEME["border"], highlightthickness=1)
        card2.pack(fill="x", pady=(0, 16))

        tk.Label(
            card2,
            text="Step 2: Personalization & Preferences",
            font=("Segoe UI Semibold", 12),
            fg=THEME["text_primary"],
            bg=THEME["bg_card"],
        ).pack(anchor="w")

        grid2 = tk.Frame(card2, bg=THEME["bg_card"])
        grid2.pack(fill="x", pady=(8, 0))

        tk.Label(grid2, text="Your Name / Greeting:", font=("Segoe UI", 9), fg=THEME["text_secondary"], bg=THEME["bg_card"]).grid(row=0, column=0, sticky="w", pady=(0, 4))
        tk.Entry(
            grid2,
            textvariable=self.user_name_var,
            font=("Segoe UI", 10),
            bg=THEME["bg_input"],
            fg=THEME["text_primary"],
            insertbackground=THEME["text_primary"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=THEME["border"],
        ).grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=(0, 12))

        tk.Label(grid2, text="Assistant Name:", font=("Segoe UI", 9), fg=THEME["text_secondary"], bg=THEME["bg_card"]).grid(row=0, column=1, sticky="w", pady=(0, 4))
        tk.Entry(
            grid2,
            textvariable=self.agent_name_var,
            font=("Segoe UI", 10),
            bg=THEME["bg_input"],
            fg=THEME["text_primary"],
            insertbackground=THEME["text_primary"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=THEME["border"],
        ).grid(row=1, column=1, sticky="ew", pady=(0, 10))

        grid2.grid_columnconfigure(0, weight=1)
        grid2.grid_columnconfigure(1, weight=1)

        # Mock Mode toggle
        tk.Checkbutton(
            card2,
            text="Enable Mock Mode (Simulate actions safely without opening real apps)",
            variable=self.mock_mode_var,
            font=("Segoe UI", 9),
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
        ).pack(anchor="w", pady=(4, 0))

    def _show_verify_result(self, ok: bool, msg: str) -> None:
        self.key_status_lbl.configure(
            text="✓ API Key Verified!" if ok else f"✕ {msg[:60]}",
            fg=THEME["emerald"] if ok else THEME["rose"],
        )
        if ok:
            self.status_label.configure(text="API key verified successfully. Ready to launch!", fg=THEME["emerald"])

    def _on_finish(self) -> None:
        key = self.api_key_var.get().strip()
        mock = self.mock_mode_var.get()
        if not key and not mock:
            res = messagebox.askyesno(
                "No API Key Entered",
                "You haven't entered a Gemini API key yet.\n\nWould you like to run in Safe Mock Mode instead?",
                parent=self.root,
            )
            if res:
                self.mock_mode_var.set(True)
                mock = True
            else:
                return

        updates = {
            "GEMINI_API_KEY": key,
            "GEMINI_MODEL": self.model_var.get().strip() or "gemini-3.8-live",
            "ZYRO_MOCK_MODE": "true" if mock else "false",
            "ZYRO_NAME": self.agent_name_var.get().strip() or "ZYRO",
            "ZYRO_USER_NAME": self.user_name_var.get().strip(),
            "ZYRO_USER_PREFERRED_NAME": self.user_name_var.get().strip(),
        }

        try:
            persist_env_values(updates)
            self.root.destroy()
            if self.on_completed:
                self.on_completed()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to save settings: {exc}", parent=self.root)

    def run(self) -> None:
        self.root.mainloop()


def launch_setup_wizard_if_needed(agent=None, on_completed=None) -> bool:
    """
    Checks if setup wizard is required (no API key and not configured).
    If required, launches wizard and returns True. Otherwise returns False.
    """
    key = getattr(agent.config, "gemini_api_key", "") if agent else ""
    mock = getattr(agent.config, "mock_mode", False) if agent else False
    
    # If already has API key or explicitly mock mode set, wizard not strictly required
    if key or (Path(".env").exists() and mock):
        return False

    wizard = ZyroSetupWizard(on_completed=on_completed)
    wizard.run()
    return True
