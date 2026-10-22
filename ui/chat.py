"""
ui/chat.py — conversation transcript widget (YOU / ZYRO / status).
Supports dark & modern theme with color tags and clean spacing.
"""
from __future__ import annotations

import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class ConversationView:
    def __init__(self, parent, *, bg: str = "#111827", fg: str = "#F9FAFB") -> None:
        self.widget = ScrolledText(
            parent,
            wrap="word",
            state="disabled",
            font=("Segoe UI", 10),
            bg=bg,
            fg=fg,
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
            highlightthickness=0,
            insertbackground=fg,
            selectbackground="#374151",
            selectforeground="#F9FAFB",
        )
        is_dark = bg.startswith("#0") or bg.startswith("#1") or bg.startswith("#2")
        
        user_lbl_color = "#38BDF8" if is_dark else "#0284C7"
        zyro_lbl_color = "#10B981" if is_dark else "#0B7A4B"
        tool_lbl_color = "#A78BFA" if is_dark else "#7C3AED"
        status_color = "#9CA3AF" if is_dark else "#6B7280"
        body_color = "#F3F4F6" if is_dark else "#1B1F24"

        self.widget.tag_configure(
            "user_label",
            font=("Segoe UI Semibold", 9),
            foreground=user_lbl_color,
            spacing1=12,
            spacing3=2,
        )
        self.widget.tag_configure(
            "user_body",
            font=("Segoe UI", 10),
            foreground=body_color,
            lmargin1=6,
            lmargin2=6,
            spacing3=8,
        )
        self.widget.tag_configure(
            "zyro_label",
            font=("Segoe UI Semibold", 9),
            foreground=zyro_lbl_color,
            spacing1=12,
            spacing3=2,
        )
        self.widget.tag_configure(
            "zyro_body",
            font=("Segoe UI", 10),
            foreground=body_color,
            lmargin1=6,
            lmargin2=6,
            spacing3=8,
        )
        self.widget.tag_configure(
            "status",
            font=("Segoe UI", 9, "italic"),
            foreground=status_color,
            lmargin1=6,
            lmargin2=6,
            spacing1=6,
            spacing3=6,
        )
        self.widget.tag_configure(
            "tool",
            font=("Consolas", 9),
            foreground=tool_lbl_color,
            lmargin1=10,
            lmargin2=10,
            spacing1=4,
            spacing3=4,
        )
        self._open_role: str | None = None

    def _edit(self, fn) -> None:
        self.widget.configure(state="normal")
        fn()
        self.widget.see(tk.END)
        self.widget.configure(state="disabled")

    def _close_open(self) -> None:
        if self._open_role is not None:
            self.widget.insert(tk.END, "\n")
            self._open_role = None

    def _timestamp(self) -> str:
        return datetime.datetime.now().strftime("%H:%M")

    def add_user(self, text: str) -> None:
        def _() -> None:
            self._close_open()
            self.widget.insert(tk.END, f"YOU  [{self._timestamp()}]\n", "user_label")
            self.widget.insert(tk.END, text.rstrip() + "\n", "user_body")

        self._edit(_)

    def append_user_voice(self, text: str) -> None:
        def _() -> None:
            if self._open_role != "YOU":
                self._close_open()
                self.widget.insert(tk.END, f"YOU  [{self._timestamp()}]\n", "user_label")
                self._open_role = "YOU"
            self.widget.insert(tk.END, text, "user_body")

        self._edit(_)

    def append_assistant(self, text: str) -> None:
        def _() -> None:
            if self._open_role != "ZYRO":
                self._close_open()
                self.widget.insert(tk.END, f"ZYRO  [{self._timestamp()}]\n", "zyro_label")
                self._open_role = "ZYRO"
            self.widget.insert(tk.END, text, "zyro_body")

        self._edit(_)

    def end_turn(self) -> None:
        def _() -> None:
            if self._open_role is not None:
                self.widget.insert(tk.END, "\n")
                self._open_role = None

        self._edit(_)

    def add_status(self, text: str) -> None:
        def _() -> None:
            self._close_open()
            self.widget.insert(tk.END, f"⚙️  ZYRO • {text}\n", "status")

        self._edit(_)

    def clear(self) -> None:
        def _() -> None:
            self.widget.delete("1.0", tk.END)
            self._open_role = None

        self._edit(_)

    def get_text(self) -> str:
        return self.widget.get("1.0", tk.END)
