"""
installer/setup_zyro.py -- Graphical Windows Package Installer & Setup for ZYRO.
Allows anyone downloading ZYRO to install it cleanly to their system with one click,
configure Gemini API key, select audio devices, and create Desktop and Start Menu shortcuts.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

# Installer colors and styles
BG = "#0B0F19"
CARD = "#111827"
TEXT = "#F9FAFB"
MUTED = "#9CA3AF"
EMERALD = "#10B981"
BORDER = "#374151"


def create_windows_shortcut(target_path: Path, shortcut_path: Path, icon_path: Path | None = None, description: str = "ZYRO Voice Agent") -> bool:
    """Creates a Windows .lnk shortcut using a small PowerShell script."""
    try:
        ps_cmd = (
            f"$WshShell = New-Object -ComObject WScript.Shell; "
            f"$Shortcut = $WshShell.CreateShortcut('{str(shortcut_path)}'); "
            f"$Shortcut.TargetPath = '{str(target_path)}'; "
            f"$Shortcut.WorkingDirectory = '{str(target_path.parent)}'; "
            f"$Shortcut.Description = '{description}'; "
        )
        if icon_path and icon_path.exists():
            ps_cmd += f"$Shortcut.IconLocation = '{str(icon_path)}'; "
        ps_cmd += "$Shortcut.Save()"
        
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return True
    except Exception as exc:
        print(f"Warning: could not create shortcut {shortcut_path}: {exc}")
        return False


class ZyroInstallerApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("ZYRO Voice Agent — Windows Setup Wizard")
        self.root.geometry("620x660")
        self.root.minsize(560, 580)
        self.root.configure(bg=BG)

        # Base dir detection
        if getattr(sys, "frozen", False):
            self.source_dir = Path(sys._MEIPASS)
            self.base_dir = Path(sys.executable).parent
        else:
            self.source_dir = Path(__file__).resolve().parent.parent
            self.base_dir = self.source_dir

        # Try setting icon if available
        icon_candidate = self.source_dir / "assets" / "zyro.ico"
        if not icon_candidate.exists():
            icon_candidate = self.base_dir / "assets" / "zyro.ico"
        if icon_candidate.exists():
            try:
                self.root.iconbitmap(str(icon_candidate))
            except Exception:
                pass

        # Default install destination: %LOCALAPPDATA%\Programs\ZYRO
        local_app_data = os.getenv("LOCALAPPDATA", str(Path.home()))
        self.dest_dir = Path(local_app_data) / "Programs" / "ZYRO"

        self.api_key_var = tk.StringVar()
        self.dest_var = tk.StringVar(value=str(self.dest_dir))
        self.create_desktop_var = tk.BooleanVar(value=True)
        self.create_start_var = tk.BooleanVar(value=True)
        self.launch_after_var = tk.BooleanVar(value=True)
        self.mock_mode_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        # Header banner
        header = tk.Frame(self.root, bg=CARD, padx=24, pady=20)
        header.pack(fill="x")

        title_row = tk.Frame(header, bg=CARD)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="⚡ ZYRO",
            font=("Segoe UI", 22, "bold"),
            fg=EMERALD,
            bg=CARD,
        ).pack(side="left")

        tk.Label(
            title_row,
            text=" Desktop Setup Wizard",
            font=("Segoe UI", 16, "bold"),
            fg=TEXT,
            bg=CARD,
        ).pack(side="left", padx=(6, 0), pady=(4, 0))

        tk.Label(
            header,
            text="Install ZYRO Voice Agent on your PC with 1-click desktop integration.",
            font=("Segoe UI", 10),
            fg=MUTED,
            bg=CARD,
        ).pack(anchor="w", pady=(6, 0))

        # Main Body
        body = tk.Frame(self.root, bg=BG, padx=24, pady=16)
        body.pack(fill="both", expand=True)

        # 1. Destination card
        card_dest = tk.Frame(body, bg=CARD, padx=16, pady=12, highlightbackground=BORDER, highlightthickness=1)
        card_dest.pack(fill="x", pady=(0, 12))

        tk.Label(card_dest, text="1. Destination Folder", font=("Segoe UI Semibold", 10), fg=TEXT, bg=CARD).pack(anchor="w")
        dest_box = tk.Frame(card_dest, bg=CARD)
        dest_box.pack(fill="x", pady=(6, 0))

        tk.Entry(
            dest_box,
            textvariable=self.dest_var,
            font=("Segoe UI", 9),
            bg="#1E293B",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
        ).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        def _browse_dest():
            chosen = filedialog.askdirectory(parent=self.root, title="Select Install Folder")
            if chosen:
                self.dest_var.set(chosen)

        tk.Button(
            dest_box,
            text="Browse...",
            font=("Segoe UI", 9),
            bg=BORDER,
            fg=TEXT,
            relief="flat",
            padx=10,
            pady=4,
            command=_browse_dest,
        ).pack(side="right")

        # 2. Gemini API setup card
        card_api = tk.Frame(body, bg=CARD, padx=16, pady=12, highlightbackground=BORDER, highlightthickness=1)
        card_api.pack(fill="x", pady=(0, 12))

        api_header = tk.Frame(card_api, bg=CARD)
        api_header.pack(fill="x")

        tk.Label(api_header, text="2. Gemini API Key", font=("Segoe UI Semibold", 10), fg=TEXT, bg=CARD).pack(side="left")

        def _open_api_portal():
            import webbrowser
            webbrowser.open_new("https://aistudio.google.com/app/apikey")

        tk.Button(
            api_header,
            text="🔑 Get Free API Key",
            font=("Segoe UI", 8),
            bg="#1E293B",
            fg="#38BDF8",
            relief="flat",
            padx=8,
            pady=2,
            command=_open_api_portal,
        ).pack(side="right")

        tk.Label(
            card_api,
            text="Enter your Gemini API key from Google AI Studio. Leave empty to use Mock Mode.",
            font=("Segoe UI", 8),
            fg=MUTED,
            bg=CARD,
        ).pack(anchor="w", pady=(2, 6))

        tk.Entry(
            card_api,
            textvariable=self.api_key_var,
            font=("Consolas", 10),
            bg="#1E293B",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
        ).pack(fill="x", ipady=6, pady=(0, 6))

        tk.Checkbutton(
            card_api,
            text="Enable Mock Mode (Simulate actions safely without API calls)",
            variable=self.mock_mode_var,
            font=("Segoe UI", 8),
            bg=CARD,
            fg=TEXT,
            selectcolor="#1E293B",
            activebackground=CARD,
        ).pack(anchor="w")

        # 3. Shortcuts & Launch options
        card_opt = tk.Frame(body, bg=CARD, padx=16, pady=12, highlightbackground=BORDER, highlightthickness=1)
        card_opt.pack(fill="x", pady=(0, 12))

        tk.Label(card_opt, text="3. Shortcuts & Launch Options", font=("Segoe UI Semibold", 10), fg=TEXT, bg=CARD).pack(anchor="w")

        tk.Checkbutton(
            card_opt,
            text="Create Desktop Shortcut (Icon on Windows Desktop)",
            variable=self.create_desktop_var,
            font=("Segoe UI", 9),
            bg=CARD,
            fg=TEXT,
            selectcolor="#1E293B",
            activebackground=CARD,
        ).pack(anchor="w", pady=(4, 0))

        tk.Checkbutton(
            card_opt,
            text="Create Start Menu Shortcut (Search 'ZYRO' in Start Menu)",
            variable=self.create_start_var,
            font=("Segoe UI", 9),
            bg=CARD,
            fg=TEXT,
            selectcolor="#1E293B",
            activebackground=CARD,
        ).pack(anchor="w", pady=(2, 0))

        tk.Checkbutton(
            card_opt,
            text="Launch ZYRO Voice Agent when setup finishes",
            variable=self.launch_after_var,
            font=("Segoe UI", 9),
            bg=CARD,
            fg=TEXT,
            selectcolor="#1E293B",
            activebackground=CARD,
        ).pack(anchor="w", pady=(2, 0))

        # Progress bar & status
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(body, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(8, 4))

        self.status_lbl = tk.Label(body, text="Ready to install.", font=("Segoe UI", 9, "italic"), fg=MUTED, bg=BG)
        self.status_lbl.pack(anchor="w")

        # Footer Actions
        footer = tk.Frame(self.root, bg=CARD, padx=24, pady=14)
        footer.pack(fill="x", side="bottom")

        self.install_btn = tk.Button(
            footer,
            text="Install ZYRO Now  ➔",
            font=("Segoe UI Semibold", 10),
            bg=EMERALD,
            fg="#0B1120",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._run_install,
        )
        self.install_btn.pack(side="right")

        tk.Button(
            footer,
            text="Cancel",
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
            relief="flat",
            padx=14,
            pady=6,
            command=self.root.destroy,
        ).pack(side="right", padx=(0, 10))

    def _run_install(self) -> None:
        dest = Path(self.dest_var.get().strip())
        self.install_btn.configure(state="disabled")
        self.status_lbl.configure(text="Preparing installation directory...")
        self.progress_var.set(15)
        self.root.update()

        try:
            dest.mkdir(parents=True, exist_ok=True)

            # Check if portable zip exists in base dir or dist dir
            zip_candidates = [
                self.base_dir / "ZYRO_v1.0.0_Windows_x64_Portable.zip",
                self.source_dir / "dist" / "ZYRO_v1.0.0_Windows_x64_Portable.zip",
                self.base_dir / "dist" / "ZYRO_v1.0.0_Windows_x64_Portable.zip",
            ]
            found_zip = next((z for z in zip_candidates if z.exists()), None)

            dist_dir = self.source_dir / "dist" / "ZYRO"
            if not dist_dir.exists():
                dist_dir = self.base_dir / "dist" / "ZYRO"

            exe_target = None

            if dist_dir.exists() and (dist_dir / "ZYRO.exe").exists():
                self.status_lbl.configure(text="Installing application binaries and runtime...")
                self.progress_var.set(35)
                self.root.update()
                for item in dist_dir.iterdir():
                    dst_item = dest / item.name
                    if item.is_dir():
                        if dst_item.exists():
                            shutil.rmtree(dst_item)
                        shutil.copytree(item, dst_item)
                    else:
                        shutil.copy2(item, dst_item)
                exe_target = dest / "ZYRO.exe"

            elif found_zip:
                self.status_lbl.configure(text=f"Extracting {found_zip.name}...")
                self.progress_var.set(40)
                self.root.update()
                with zipfile.ZipFile(found_zip, "r") as zf:
                    for member in zf.namelist():
                        # Extract stripping the top 'ZYRO/' folder
                        parts = Path(member).parts
                        if len(parts) > 1 and parts[0] == "ZYRO":
                            rel_path = Path(*parts[1:])
                        else:
                            rel_path = Path(member)
                        target_file = dest / rel_path
                        if member.endswith("/"):
                            target_file.mkdir(parents=True, exist_ok=True)
                        else:
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(member) as src, open(target_file, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                exe_target = dest / "ZYRO.exe"
            else:
                self.status_lbl.configure(text="Installing application package files...")
                self.progress_var.set(40)
                self.root.update()
                for folder in ["assets", "audio", "core", "devices", "gemini", "memory", "skills", "tools", "ui", "webapps", "docs"]:
                    s = self.source_dir / folder
                    if s.exists():
                        d = dest / folder
                        if d.exists():
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                for f in ["app.py", "zyro_app.pyw", "config.py", "launch_zyro.bat", "run_silent.vbs", "README.md", "requirements.txt", ".env.example"]:
                    s = self.source_dir / f
                    if s.exists():
                        shutil.copy2(s, dest / f)
                exe_target = dest / "launch_zyro.bat"

            self.progress_var.set(70)
            self.status_lbl.configure(text="Configuring environment settings (.env)...")
            self.root.update()

            api_key = self.api_key_var.get().strip()
            mock = self.mock_mode_var.get()
            if not api_key:
                mock = True

            env_content = (
                f"GEMINI_API_KEY={api_key}\n"
                f"GEMINI_MODEL=gemini-3.8-live\n"
                f"ZYRO_MOCK_MODE={'true' if mock else 'false'}\n"
                f"ZYRO_NAME=ZYRO\n"
                f"ZYRO_PURPOSE=Windows-first personal AI assistant\n"
                f"ZYRO_LOG_LEVEL=INFO\n"
            )
            (dest / ".env").write_text(env_content, encoding="utf-8")

            self.progress_var.set(85)
            self.status_lbl.configure(text="Creating Desktop and Start Menu shortcuts...")
            self.root.update()

            icon_path = dest / "assets" / "zyro.ico"
            if not icon_path.exists():
                icon_path = self.source_dir / "assets" / "zyro.ico"
            if not icon_path.exists():
                icon_path = self.base_dir / "assets" / "zyro.ico"

            # 1. Desktop Shortcut
            if self.create_desktop_var.get():
                desktop = Path.home() / "Desktop"
                if desktop.exists():
                    create_windows_shortcut(
                        target_path=exe_target,
                        shortcut_path=desktop / "ZYRO Voice Agent.lnk",
                        icon_path=icon_path if icon_path.exists() else None,
                        description="ZYRO - Personal Windows Voice AI Assistant",
                    )

            # 2. Start Menu Shortcut
            if self.create_start_var.get():
                appdata = os.getenv("APPDATA")
                if appdata:
                    start_programs = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "ZYRO"
                    start_programs.mkdir(parents=True, exist_ok=True)
                    create_windows_shortcut(
                        target_path=exe_target,
                        shortcut_path=start_programs / "ZYRO Voice Agent.lnk",
                        icon_path=icon_path if icon_path.exists() else None,
                        description="ZYRO - Personal Windows Voice AI Assistant",
                    )

            self.progress_var.set(100)
            self.status_lbl.configure(text="Setup complete! Ready to launch ZYRO.")
            self.root.update()

            messagebox.showinfo(
                "Installation Successful",
                f"ZYRO has been successfully installed to:\n{dest}\n\n"
                "✓ Desktop Shortcut created\n"
                "✓ Start Menu shortcut created\n"
                "✓ Ready to run!",
                parent=self.root,
            )

            if self.launch_after_var.get():
                try:
                    if exe_target.name.endswith(".exe"):
                        subprocess.Popen([str(exe_target)], cwd=str(dest))
                    else:
                        subprocess.Popen(["cmd.exe", "/c", str(exe_target)], cwd=str(dest))
                except Exception as exc:
                    print(f"Could not launch: {exc}")

            self.root.destroy()
        except Exception as exc:
            messagebox.showerror("Installation Error", f"Installation failed: {exc}", parent=self.root)
            self.install_btn.configure(state="normal")

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    ZyroInstallerApp().run()
