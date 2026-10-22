"""
ui/main_window.py — ZYRO Modern Desktop Assistant Window.

Chat + voice share the same Gemini Live session. Live/mic/playback run on a
background thread; every widget update is marshalled onto Tkinter via after().
Includes modern dark theme, audio visualizer, quick action chips, and device pills.
"""
from __future__ import annotations

import asyncio
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ui.chat import ConversationView
from ui.theme import THEME, ModernVisualizerCanvas

logger = logging.getLogger("zyro.ui")

BG = THEME["bg_dark"]
CARD = THEME["bg_card"]
TEXT = THEME["text_primary"]
MUTED = THEME["text_secondary"]
ACCENT = THEME["emerald"]
BORDER = THEME["border"]
LIVE_GREEN = THEME["emerald"]
OFF_RED = THEME["rose"]


def _tool_status_line(name: str, args: dict) -> str:
    if name == "open_application":
        return f"Opening {args.get('name', 'application')}..."
    if name == "open_file":
        return "Opening file..."
    if name == "open_folder":
        return "Opening folder..."
    if name == "web_search":
        return f"Searching the web for \"{args.get('query', 'that')}\"..."
    if name == "open_url":
        return f"Opening {args.get('url', 'webpage')}..."
    if name == "read_webpage":
        return f"Reading {args.get('url', 'webpage')}..."
    if name in ("open_youtube", "search_youtube"):
        q = args.get("query", "")
        return f"Searching YouTube for \"{q}\"..." if q else "Opening YouTube..."
    if name in ("open_spotify", "search_spotify"):
        q = args.get("query", "")
        return f"Searching Spotify for \"{q}\"..." if q else "Opening Spotify..."
    if name == "remember_memory":
        return f"Saving memory: {args.get('key', '')}..."
    if name == "recall_memory":
        return f"Recalling: {args.get('key', '')}..."
    if name == "search_memory":
        return f"Searching memory for \"{args.get('query', '')}\"..."
    if name == "forget_memory":
        return f"Forgetting: {args.get('key', '')}..."
    # Desktop control
    if name == "close_window":
        app = args.get('app_name', '') or 'active window'
        return f"Closing {app}..."
    if name == "switch_app":
        return "Switching application..."
    if name == "minimize_window":
        app = args.get('app_name', '') or 'window'
        return f"Minimizing {app}..."
    if name == "maximize_window":
        app = args.get('app_name', '') or 'window'
        return f"Maximizing {app}..."
    if name == "restore_window":
        app = args.get('app_name', '') or 'window'
        return f"Restoring {app}..."
    if name == "focus_application":
        return f"Focusing {args.get('app_name', 'application')}..."
    # Browser control
    if name == "next_browser_tab":
        return "Switching to next tab..."
    if name == "previous_browser_tab":
        return "Switching to previous tab..."
    if name == "close_browser_tab":
        return "Closing browser tab..."
    if name == "open_new_browser_tab":
        return "Opening new browser tab..."
    if name == "switch_to_browser_tab":
        return f"Switching to tab {args.get('tab_number', '')}..."
    # Media control
    if name == "media_play":
        return "Playing media..."
    if name == "media_pause":
        return "Pausing media..."
    if name == "media_play_pause":
        return "Toggling media playback..."
    if name == "media_next":
        return "Skipping to next track..."
    if name == "media_previous":
        return "Going to previous track..."
    if name == "media_volume_up":
        return "Increasing volume..."
    if name == "media_volume_down":
        return "Decreasing volume..."
    if name == "media_mute":
        return "Muting audio..."
    if name == "media_unmute":
        return "Unmuting audio..."
    # Windows system
    if name == "open_windows_settings":
        return f"Opening {args.get('category', 'settings')} settings..."
    if name == "open_system_utility":
        return f"Opening {args.get('utility', 'utility').replace('_', ' ').title()}..."
    if name == "open_special_folder":
        return f"Opening {args.get('folder', 'folder').replace('_', ' ').title()}..."
    if name == "zyro_sleep":
        return "Going to sleep..."
    # Instagram
    if name == "open_instagram":
        return "Opening Instagram..."
    if name == "search_instagram":
        return f"Searching Instagram for \"{args.get('query', 'that')}\"..."
    if name == "open_instagram_profile":
        u = args.get("username", "") or "profile"
        return f"Opening Instagram profile @{u}..." if u else "Opening Instagram profile..."
    if name == "open_instagram_reels":
        u = args.get("username", "") or ""
        return f"Opening reels for @{u}..." if u else "Opening Instagram reels..."
    if name == "open_instagram_post":
        u = args.get("username", "") or ""
        return f"Opening posts for @{u}..." if u else "Opening Instagram posts..."
    if name == "refresh_instagram":
        return "Refreshing Instagram..."
    # Discord
    if name == "open_discord":
        return "Opening Discord..."
    if name == "open_discord_server":
        return f"Opening Discord server \"{args.get('server_name', '')}\"..."
    if name == "open_discord_channel":
        return f"Opening Discord channel \"{args.get('channel_name', '')}\"..."
    if name == "search_discord":
        return f"Searching Discord for \"{args.get('query', 'that')}\"..."
    if name == "send_discord_message":
        msg = args.get("message", "")
        return f"Sending Discord message: \"{msg[:30]}{'...' if len(msg) > 30 else ''}\"..."
    # WhatsApp
    if name == "open_whatsapp":
        return "Opening WhatsApp Web..."
    if name == "search_whatsapp_contact":
        return f"Searching WhatsApp for \"{args.get('contact_name', '')}\"..."
    if name == "open_whatsapp_contact":
        return f"Opening WhatsApp contact \"{args.get('contact_name', '')}\"..."
    if name == "send_whatsapp_message":
        c = args.get("contact_name", "") or "contact"
        msg = args.get("message", "")
        return f"Sending WhatsApp message to {c}: \"{msg[:25]}{'...' if len(msg) > 25 else ''}\"..."
    # Shared webapp nav
    if name == "scroll_webapp":
        d = args.get("direction", "down")
        a = args.get("amount", "medium")
        return f"Scrolling {d} ({a})..."
    if name == "go_back_webapp":
        return "Going back..."
    if name == "go_forward_webapp":
        return "Going forward..."
    if name == "refresh_webapp":
        return f"Refreshing {args.get('app', 'page').title() or 'page'}..."
    # YouTube webapp
    if name == "open_youtube_webapp":
        return "Opening YouTube..."
    if name == "search_youtube_webapp":
        return f"Searching YouTube for \"{args.get('query', 'that')}\"..."
    # Spotify webapp
    if name == "open_spotify_webapp":
        return "Opening Spotify..."
    if name == "search_spotify_webapp":
        return f"Searching Spotify for \"{args.get('query', 'that')}\"..."
    return f"Running {name}..."


class ZyroMainWindow:
    def __init__(self, agent, start_voice: bool = False) -> None:
        self.agent = agent
        self.root = tk.Tk()
        self.root.title(f"{agent.config.zyro_name} — Desktop AI Voice Assistant")
        self.root.geometry("620x790")
        self.root.minsize(500, 640)
        self.root.configure(bg=BG)

        # Apply application icon if present
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "zyro.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        self._voice_loop: asyncio.AbstractEventLoop | None = None
        self._voice_task: asyncio.Task | None = None
        self._sending = False

        self._build()
        if start_voice:
            self.status_var.set("Starting")
            threading.Thread(target=self._run_voice, name="zyro-voice", daemon=True).start()

        # Register sleep/wake state callbacks for UI updates.
        state_mgr = getattr(agent, "state_manager", None)
        if state_mgr is not None:
            state_mgr.on_change(self._on_state_change)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Top Header Bar Card
        top_card = tk.Frame(self.root, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        top_card.pack(fill="x", padx=16, pady=(14, 8))

        header_inner = tk.Frame(top_card, bg=CARD, padx=16, pady=12)
        header_inner.pack(fill="x")

        # Left: Logo & Title
        title_box = tk.Frame(header_inner, bg=CARD)
        title_box.pack(side="left")

        logo_title_row = tk.Frame(title_box, bg=CARD)
        logo_title_row.pack(anchor="w")

        tk.Label(
            logo_title_row,
            text="⚡ " + self.agent.config.zyro_name,
            font=("Segoe UI", 18, "bold"),
            fg=THEME["emerald"],
            bg=CARD,
        ).pack(side="left")

        live = not self.agent.config.mock_mode
        mode_badge = tk.Frame(
            logo_title_row,
            bg=THEME["bg_card_elevated"],
            padx=8,
            pady=2,
            highlightbackground=LIVE_GREEN if live else THEME["amber"],
            highlightthickness=1,
        )
        mode_badge.pack(side="left", padx=(10, 0))

        self._mode_dot = tk.Label(
            mode_badge,
            text="●",
            fg=LIVE_GREEN if live else THEME["amber"],
            bg=THEME["bg_card_elevated"],
            font=("Segoe UI", 8),
        )
        self._mode_dot.pack(side="left")

        tk.Label(
            mode_badge,
            text=" LIVE" if live else " MOCK",
            fg=LIVE_GREEN if live else THEME["amber"],
            bg=THEME["bg_card_elevated"],
            font=("Segoe UI Semibold", 8),
        ).pack(side="left")

        # Subtitle / Model Tag
        tk.Label(
            title_box,
            text=f"Model: {self.agent.config.gemini_model} · Windows Agent",
            font=("Segoe UI", 9),
            fg=MUTED,
            bg=CARD,
        ).pack(anchor="w", pady=(2, 0))

        # Right: Status pill
        status_box = tk.Frame(header_inner, bg=CARD)
        status_box.pack(side="right")

        self.status_var = tk.StringVar(value="Idle")
        self.status_pill = tk.Label(
            status_box,
            textvariable=self.status_var,
            font=("Segoe UI Semibold", 10),
            fg=THEME["cyan"],
            bg=THEME["bg_input"],
            padx=12,
            pady=4,
            relief="flat",
            bd=0,
        )
        self.status_pill.pack(side="right")

        # Audio Visualizer Bar
        viz_wrap = tk.Frame(self.root, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        viz_wrap.pack(fill="x", padx=16, pady=(0, 8))
        self.visualizer = ModernVisualizerCanvas(viz_wrap, height=36)
        self.visualizer.pack(fill="x", expand=True, padx=6, pady=4)

        # Device Status Mini Ribbon
        devices_row = tk.Frame(self.root, bg=BG)
        devices_row.pack(fill="x", padx=18, pady=(0, 6))

        self.mic_var = tk.StringVar(value="Microphone: ● Starting")
        self.spk_var = tk.StringVar(value="Speaker: ● Ready")
        self.cam_var = tk.StringVar(value="Camera: OFF")

        mic_lbl = tk.Label(devices_row, textvariable=self.mic_var, font=("Segoe UI", 8), fg=MUTED, bg=BG)
        mic_lbl.pack(side="left", padx=(0, 12))

        spk_lbl = tk.Label(devices_row, textvariable=self.spk_var, font=("Segoe UI", 8), fg=MUTED, bg=BG)
        spk_lbl.pack(side="left", padx=(0, 12))

        self._cam_label = tk.Label(devices_row, textvariable=self.cam_var, font=("Segoe UI", 8, "bold"), fg=OFF_RED, bg=BG)
        self._cam_label.pack(side="left")

        # Quick Action Chips Ribbon
        chips_bar = tk.Frame(self.root, bg=BG)
        chips_bar.pack(fill="x", padx=16, pady=(0, 6))

        chips = [
            ("🌐 Web", lambda: self.send_message("Search the web for latest tech news")),
            ("🎵 Spotify", lambda: self.send_message("Play top hits on Spotify")),
            ("💬 WhatsApp", lambda: self.send_message("Open WhatsApp")),
            ("📁 Documents", lambda: self.send_message("Find files in Documents")),
            ("💤 Sleep", self._toggle_sleep),
            ("🗑 Clear", self._clear_chat),
        ]

        for text, cmd in chips:
            chip = tk.Button(
                chips_bar,
                text=text,
                font=("Segoe UI", 8),
                bg=THEME["bg_card"],
                fg=THEME["text_secondary"],
                activebackground=THEME["border"],
                activeforeground=TEXT,
                relief="flat",
                bd=0,
                padx=8,
                pady=2,
                cursor="hand2",
                command=cmd,
            )
            chip.pack(side="left", padx=(0, 6))

        # Chat Area
        chat_wrap = tk.Frame(self.root, bg=BORDER, padx=1, pady=1)
        chat_wrap.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        self.chat = ConversationView(chat_wrap, bg=CARD, fg=TEXT)
        self.chat.widget.pack(fill="both", expand=True)

        # Message Input Composer
        composer = tk.Frame(self.root, bg=BG)
        composer.pack(fill="x", padx=16, pady=(0, 8))

        self.input_var = tk.StringVar()
        self.entry = tk.Entry(
            composer,
            textvariable=self.input_var,
            font=("Segoe UI", 11),
            relief="flat",
            bg=CARD,
            fg=TEXT,
            insertbackground=TEXT,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        self.entry.insert(0, "")
        self.entry.bind("<Return>", self._on_enter)
        self.placeholder = "Type a message or speak into your microphone..."
        self._placeholder_on = True
        self._set_placeholder()
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)

        self.send_btn = tk.Button(
            composer,
            text="Send ➔",
            font=("Segoe UI Semibold", 10),
            bg=ACCENT,
            fg="#0B1120",
            activebackground=THEME["emerald_glow"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.send_message,
        )
        self.send_btn.pack(side="right")

        # Footer Actions
        footer = tk.Frame(self.root, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        footer.pack(fill="x", side="bottom")

        footer_inner = tk.Frame(footer, bg=CARD, padx=16, pady=8)
        footer_inner.pack(fill="x")

        tk.Button(
            footer_inner,
            text="🎙 Devices",
            font=("Segoe UI", 9),
            bg=THEME["bg_input"],
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=4,
            command=self._open_devices,
        ).pack(side="left")

        self._sleep_btn = tk.Button(
            footer_inner,
            text="Sleep",
            font=("Segoe UI", 9),
            bg=THEME["bg_input"],
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=4,
            command=self._toggle_sleep,
        )
        self._sleep_btn.pack(side="left", padx=(8, 0))

        tk.Button(
            footer_inner,
            text="📋 Copy Chat",
            font=("Segoe UI", 9),
            bg=THEME["bg_input"],
            fg=TEXT,
            relief="flat",
            padx=10,
            pady=4,
            command=self._copy_chat,
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            footer_inner,
            text="⚙ Settings & API",
            font=("Segoe UI Semibold", 9),
            bg=THEME["bg_input"],
            fg=THEME["cyan"],
            relief="flat",
            padx=14,
            pady=4,
            command=self._open_settings,
        ).pack(side="right")

        self._refresh_device_status()

    def _set_placeholder(self) -> None:
        if not self.input_var.get():
            self._placeholder_on = True
            self.entry.configure(fg=MUTED)
            self.input_var.set(self.placeholder)

    def _clear_placeholder(self, _event=None) -> None:
        if self._placeholder_on:
            self._placeholder_on = False
            self.input_var.set("")
            self.entry.configure(fg=TEXT)

    def _restore_placeholder(self, _event=None) -> None:
        if not self.input_var.get().strip():
            self._set_placeholder()

    def _on_enter(self, _event=None):
        self.send_message()
        return "break"

    def _ui(self, fn) -> None:
        self.root.after(0, fn)

    def _clear_chat(self) -> None:
        if hasattr(self.chat, "clear"):
            self.chat.clear()

    def _copy_chat(self) -> None:
        text = self.chat.get_text()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", "Conversation transcript copied to clipboard!", parent=self.root)

    def _set_status(self, text: str) -> None:
        def _() -> None:
            self.status_var.set(text)
            if hasattr(self, "visualizer"):
                self.visualizer.set_state(text)

            if text == "Listening":
                self.status_pill.configure(fg=THEME["cyan"])
                self.mic_var.set("Microphone: ● Listening")
                self._set_sending(False)
            elif text == "Speaking":
                self.status_pill.configure(fg=THEME["emerald"])
                self.mic_var.set("Microphone: ● Speaking")
            elif text == "Running tool":
                self.status_pill.configure(fg=THEME["amber"])
                self.mic_var.set("Microphone: ● Tool running")
            elif text == "Error":
                self.status_pill.configure(fg=THEME["rose"])
                self.mic_var.set("Microphone: ○ Error")
            elif text == "Sleeping":
                self.status_pill.configure(fg=THEME["text_muted"])
                self.mic_var.set("Microphone: ○ Sleeping")
                if hasattr(self, "_sleep_btn"):
                    self._sleep_btn.configure(text="Wake")
            elif text in ("ZYRO is awake.", "Listening"):
                self.status_pill.configure(fg=THEME["cyan"])
                if hasattr(self, "_sleep_btn"):
                    self._sleep_btn.configure(text="Sleep")

        self._ui(_)

    def _set_sending(self, sending: bool) -> None:
        self._sending = sending
        state = "disabled" if sending else "normal"
        self.send_btn.configure(state=state)
        self.entry.configure(state=state)

    def send_message(self, text: str | None = None) -> bool:
        raw = text if text is not None else self.input_var.get()
        if self._placeholder_on and text is None:
            return False
        cleaned = (raw or "").strip()
        if not cleaned or cleaned == self.placeholder:
            return False
        if not self.agent.live_client.submit_text(cleaned):
            self.status_var.set("Not connected")
            return False
        self.chat.add_user(cleaned)
        self._placeholder_on = False
        self.input_var.set("")
        self.entry.configure(fg=TEXT)
        self._set_sending(True)
        self.status_var.set("Thinking")
        if hasattr(self, "visualizer"):
            self.visualizer.set_state("thinking")
        return True

    def _on_user_voice(self, text: str) -> None:
        self._ui(lambda: self.chat.append_user_voice(text))

    def _on_assistant(self, text: str) -> None:
        def _() -> None:
            self.chat.append_assistant(text)
            self._set_sending(False)

        self._ui(_)

    def _on_turn_end_status(self, text: str) -> None:
        if text == "Listening":
            self._ui(self.chat.end_turn)
        self._set_status(text)

    def _on_tool(self, name: str, args: dict) -> None:
        line = _tool_status_line(name, args)
        self._ui(lambda: self.chat.add_status(line))

    def _refresh_device_status(self) -> None:
        ds = self.agent.device_state
        mic = ds.mic_name if ds.mic_name else "System default"
        spk = ds.speaker_name if ds.speaker_name else "System default"
        listening = self.status_var.get() in {"Listening", "Speaking", "Running tool", "Connected", "Starting"}
        mic_icon = "●" if listening else "○"
        self.mic_var.set(f"Mic: {mic_icon} {mic}")
        self.spk_var.set(f"Spk: ● {spk}")
        if ds.camera_enabled:
            self.cam_var.set(f"Cam: ON · {ds.camera_name}")
            self._cam_label.configure(fg=LIVE_GREEN)
        else:
            extra = f" · {ds.camera_name}" if ds.camera_name else ""
            self.cam_var.set(f"Cam: OFF{extra}")
            self._cam_label.configure(fg=OFF_RED)

    def _on_state_change(self, old_state, new_state) -> None:
        """StateManager callback -- marshalled to UI thread via after()."""
        from core.zyro_state import ZyroState

        def _update():
            if new_state == ZyroState.SLEEPING:
                self.status_var.set("Sleeping -- say 'Hey ZYRO, wake up'")
                self.mic_var.set("Microphone: \u25cb Sleeping")
                if hasattr(self, "visualizer"):
                    self.visualizer.set_state("sleeping")
                if hasattr(self, "_sleep_btn"):
                    self._sleep_btn.configure(text="Wake")
            elif new_state == ZyroState.ACTIVE:
                self.status_var.set("Listening")
                if hasattr(self, "visualizer"):
                    self.visualizer.set_state("listening")
                if hasattr(self, "_sleep_btn"):
                    self._sleep_btn.configure(text="Sleep")

        self._ui(_update)

    def _toggle_sleep(self) -> None:
        """Sleep/Wake button pressed -- use centralized StateManager."""
        state_mgr = getattr(self.agent, "state_manager", None)
        if state_mgr is None:
            return
        if state_mgr.is_sleeping():
            state_mgr.set_active()
        else:
            state_mgr.set_sleeping()

    def _open_settings(self) -> None:
        from ui.settings import open_settings_window

        open_settings_window(self.root, self.agent)

    def _open_devices(self) -> None:
        from ui.devices import open_devices_window

        open_devices_window(self.root, self.agent, on_applied=self._refresh_device_status)

    def _run_voice(self) -> None:
        loop = asyncio.new_event_loop()
        self._voice_loop = loop
        asyncio.set_event_loop(loop)

        async def _session() -> None:
            await self.agent.run_voice(
                on_text_out=self._on_assistant,
                on_user_text=self._on_user_voice,
                on_status=self._on_turn_end_status,
                on_tool=self._on_tool,
            )

        try:
            self._voice_task = loop.create_task(_session())
            loop.run_until_complete(self._voice_task)
        except asyncio.CancelledError:
            logger.info("Voice session cancelled")
        except Exception:
            logger.exception("Voice session failed")
            self._set_status("Error")
        finally:
            self._voice_task = None
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                logger.debug("Error while draining voice loop tasks", exc_info=True)
            loop.close()
            self._voice_loop = None

    def _on_close(self) -> None:
        loop = self._voice_loop
        task = self._voice_task
        if loop is not None and task is not None and loop.is_running():
            loop.call_soon_threadsafe(task.cancel)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def launch_ui(agent, start_voice: bool = False) -> None:
    ZyroMainWindow(agent, start_voice=start_voice).run()
