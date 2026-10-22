@echo off
rem ==============================================================================
rem Launch ZYRO Graphical Windows Package Installer & Setup
rem ==============================================================================
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" installer\setup_zyro.py
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" installer\setup_zyro.py
    exit /b 0
)

start "" python installer\setup_zyro.py
