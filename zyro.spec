# -*- mode: python ; coding: utf-8 -*-
"""
zyro.spec -- PyInstaller specification file for ZYRO Desktop Voice Agent.
Compiles a standalone Windows GUI application with bundled assets and dependencies.
"""
import os
import sys
from pathlib import Path

block_cipher = None
project_root = Path(os.path.abspath(SPECPATH))

added_files = [
    (str(project_root / "assets"), "assets"),
    (str(project_root / "ZYRO_MASTER_PROMPT.md"), "."),
    (str(project_root / ".env.example"), "."),
]

# Add optional data folder if present
if (project_root / "data").exists():
    added_files.append((str(project_root / "data"), "data"))

hidden_imports = [
    "google.genai",
    "google.genai.types",
    "sounddevice",
    "numpy",
    "bs4",
    "requests",
    "dotenv",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "docx",
    "asyncio",
    "sqlite3",
    "ctypes",
    "ctypes.wintypes",
    "pyautogui",
    "pygetwindow",
    "win32gui",
    "win32con",
    "win32api",
    "win32process",
    "win32com",
    "win32com.client",
]

a = Analysis(
    ["zyro_app.pyw"],
    pathex=[str(project_root)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytest_asyncio"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ZYRO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No CMD window!
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "assets" / "zyro.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ZYRO",
)
