@echo off
rem ==============================================================================
rem ZYRO Desktop Voice Agent - Windows Quick Launcher
rem Launches ZYRO as a native desktop app with zero command prompt window.
rem ==============================================================================

cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" zyro_app.pyw
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" app.py
    exit /b 0
)

where pythonw >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" pythonw zyro_app.pyw
    exit /b 0
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" python app.py
    exit /b 0
)

echo [ERROR] Python not found. Please install Python 3.10+ or run setup.
pause
