"""
ui/theme.py -- Modern styling, palettes, fonts, and visualizer components for ZYRO.
"""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

# Modern Dark Obsidian Theme (Cyan & Emerald accents)
THEME = {
    "bg_dark": "#0B0F19",        # Deep obsidian window background
    "bg_card": "#111827",        # Card / panel background
    "bg_card_elevated": "#1F2937",# Hover / elevated card background
    "bg_input": "#1E293B",       # Text input background
    "border": "#374151",         # Subtle card border
    "border_focus": "#10B981",   # Emerald focus highlight
    
    # Text colors
    "text_primary": "#F9FAFB",   # Pure bright white-gray
    "text_secondary": "#9CA3AF", # Muted gray
    "text_muted": "#64748B",     # Extra muted slate
    
    # Accent colors
    "emerald": "#10B981",        # Emerald green (live / success / primary)
    "emerald_glow": "#059669",
    "cyan": "#06B6D4",           # Electric cyan (accent / listening)
    "amber": "#F59E0B",          # Warm amber (thinking / warning)
    "rose": "#F43F5E",           # Rose red (muted / error / off)
    "violet": "#8B5CF6",         # Violet (speaking / AI personality)
    
    # User / Agent message bubble tags
    "user_bubble": "#1E293B",
    "user_accent": "#38BDF8",
    "zyro_bubble": "#13232C",
    "zyro_accent": "#10B981",
    "tool_bubble": "#1E1B4B",
    "tool_accent": "#A78BFA",
}

FONT_HEADING = ("Segoe UI", 16, "bold")
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI", 10, "normal")
FONT_BODY = ("Segoe UI", 10)
FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
FONT_CODE = ("Consolas", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_STATUS = ("Segoe UI", 9, "italic")


class ModernVisualizerCanvas(tk.Canvas):
    """
    Animated audio visualizer bar / waveform responding to agent state.
    """
    def __init__(self, parent, width: int = 480, height: int = 42, **kwargs) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=THEME["bg_card"],
            highlightthickness=0,
            **kwargs
        )
        self.bar_count = 28
        self._phase = 0.0
        self._state = "idle"
        self._animating = True
        self._draw_frame()

    def set_state(self, state: str) -> None:
        self._state = state.lower()

    def _draw_frame(self) -> None:
        if not self.winfo_exists():
            return
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1:
            w = 480
        if h <= 1:
            h = 42

        mid_y = h / 2.0
        bar_w = max(4, int(w / (self.bar_count * 1.6)))
        spacing = (w - (self.bar_count * bar_w)) / (self.bar_count + 1)

        # Activity level multiplier based on state
        if "listen" in self._state:
            color = THEME["cyan"]
            base_amp = 0.65
            speed = 0.18
        elif "speak" in self._state:
            color = THEME["emerald"]
            base_amp = 0.85
            speed = 0.24
        elif "think" in self._state or "running" in self._state:
            color = THEME["amber"]
            base_amp = 0.45
            speed = 0.12
        elif "sleep" in self._state:
            color = THEME["text_muted"]
            base_amp = 0.08
            speed = 0.04
        else:
            color = THEME["emerald_glow"]
            base_amp = 0.18
            speed = 0.08

        self._phase += speed

        for i in range(self.bar_count):
            x = spacing + i * (bar_w + spacing)
            # Combine two sine waves for organic sound wave motion
            wave = (
                math.sin(self._phase + i * 0.4) * 0.6 +
                math.sin(self._phase * 0.7 - i * 0.3) * 0.4
            )
            bar_h = max(4, int(abs(wave) * (h * 0.42 * base_amp) + 4))
            y1 = mid_y - bar_h
            y2 = mid_y + bar_h
            
            # Rounded capsule representation
            self.create_rectangle(
                x, y1, x + bar_w, y2,
                fill=color,
                outline="",
                width=0
            )

        self.after(40, self._draw_frame)
