# Changelog

All notable changes to the **ZYRO Voice Agent** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-22

### Added
- **Standalone Desktop Application**:
  - Windows windowed execution entry point `zyro_app.pyw` for zero console/terminal popup.
  - Windows batch quick launcher `launch_zyro.bat` and silent VBScript launcher `run_silent.vbs`.
  - Modern high-resolution application icon set `assets/zyro.ico` and `assets/zyro.png` (256x256 multi-layer Windows ICO).
- **High-Polish Modern Desktop UI**:
  - Deep obsidian dark theme (`ui/theme.py`) with cyber emerald (`#10B981`) and electric cyan (`#06B6D4`) accents.
  - Real-time animated audio visualizer waveform canvas (`ModernVisualizerCanvas`) responding dynamically to listening, speaking, thinking, and sleeping states.
  - Quick action chips ribbon for one-click access: Web Search, Spotify, WhatsApp, Documents, Sleep/Wake, and Clear Chat.
  - Device status mini-ribbon displaying real-time microphone, speaker, and camera state.
  - One-click "Copy Chat" transcript export button and chat history formatting with user and agent timestamps.
- **Interactive In-App Settings & Gemini API Configuration**:
  - Fully revamped `ui/settings.py` replacing static read-only text with an interactive configuration center.
  - Inline Gemini API Key password box with show/hide toggle and instant "Test Connection" button testing Google GenAI live.
  - Gemini Model dropdown picker (`gemini-3.8-live`, `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`).
  - Safe Mock Mode switch allowing toggling between simulated and real Windows actions.
  - Assistant Persona & Identity customization (Agent Name, User Name, Preferred Greeting Name, Purpose).
  - Search Folders manager with folder browser dialog to add or remove indexed directories.
  - Direct atomic `.env` persistence updating both disk and running in-memory agent configuration.
- **First-Run Guided Setup Wizard (`ui/setup_wizard.py`)**:
  - Automated first-time setup window triggered when starting with an unconfigured API key or via `--setup`.
  - Direct hyperlink to Google AI Studio to acquire a free Gemini API key.
  - Guided step-by-step verification, device check, and personality setup.
- **Standalone Packaging & Windows Installer**:
  - PyInstaller specification `zyro.spec` configured for `--windowed --noconsole` executable compilation with asset bundling.
  - Automated build script `build_exe.py` compiling `dist/ZYRO/ZYRO.exe`.
  - Graphical Windows package installer `installer/setup_zyro.py` allowing custom install paths, `.env` generation, and Desktop & Start Menu `.lnk` shortcut creation.
  - Inno Setup compiler script `installer/zyro_setup.iss` for building enterprise `ZYRO_Setup_v1.0.exe` installers.
  - Automated portable zip packager `package_release.py`.
- **Complete Microsoft Word (.docx) Documentation Suite**:
  - `ZYRO_Architecture_and_Technical_Specification.docx`: Comprehensive system architecture, PortAudio pipeline, and security model.
  - `ZYRO_User_Guide_and_Desktop_Manual.docx`: End-user manual with full voice command catalog and UI guide.
  - `ZYRO_Setup_and_Deployment_Guide.docx`: Installation, Gemini API acquisition, and standalone compilation instructions.
  - `ZYRO_Open_Source_Contributor_Guide.docx`: Architecture conventions, adding tools in 5 minutes, and PR guide.
  - `ZYRO_API_and_Tools_Reference.docx`: Exhaustive reference of 30+ registered agent tools and permission tiers.
  - Automated generation script `docs/generate_docx_suite.py`.
- **Open Source Repository Governance**:
  - MIT License in `LICENSE`.
  - Contributor guidelines in `CONTRIBUTING.md`.
  - Code of Conduct in `CODE_OF_CONDUCT.md`.
  - Security vulnerability reporting policy in `SECURITY.md`.

---

## [0.3.0] - 2026-09-28

### Added
- **Browser & Web Application Automation Layer**:
  - Added `webapps/browser_adapter.py` providing unified browser tab navigation and input synthesis.
  - Implemented `tools/whatsapp_web.py` for WhatsApp Web search, contact selection, and automated messaging.
  - Implemented `tools/discord_web.py` for Discord server and channel navigation.
  - Added shared web app navigation tools: `scroll_webapp`, `go_back_webapp`, `go_forward_webapp`, `refresh_webapp`.
  - Added Instagram tools in `tools/instagram.py` (search, profiles, reels, posts).
  - Added Spotify and YouTube web application launchers and search tools.
- **Chained Multi-Turn Tool Execution**:
  - Support for multi-step tool workflows (e.g., search contact -> select contact -> type message -> send).

---

## [0.2.0] - 2026-09-19

### Added
- **Windows Desktop Control Tools**:
  - Implemented `tools/desktop_control.py` for window switching (`Alt+Tab`), closing, minimizing, maximizing, and restoring windows.
  - Implemented `tools/browser_control.py` for native browser tab switching (`Ctrl+Tab`, `Ctrl+Shift+Tab`, `Ctrl+W`, `Ctrl+T`).
- **Media & System Audio Control**:
  - Implemented `tools/media_control.py` for global Windows media keys (Play/Pause, Next Track, Previous Track, Volume Up, Volume Down, Mute).
- **Windows System Settings & Utilities**:
  - Implemented `tools/windows_system.py` providing voice navigation to Windows Settings pages, Task Manager, Control Panel, and special user folders.
- **Sleep & Wake Word Management**:
  - Added centralized `core/zyro_state.py` StateManager.
  - Added voice sleep and wake commands ("Hey ZYRO, go to sleep", "Hey ZYRO, wake up").
  - Local SAPI wake word detection support via pywin32.

---

## [0.1.0] - 2026-09-16

### Added
- Initial project prototype and architecture skeleton.
- Core `ZyroAgent` class with Google Gemini Live API integration via `google-genai` SDK.
- Full-duplex PortAudio voice capture (`audio/mic.py`) and playback (`audio/player.py`).
- Three-tier permission security model (`READ_ONLY`, `USER_ACTION`, `SYSTEM_WRITE`).
- SQLite persistent user memory store (`memory/sqlite_memory.py`).
- File search and application launcher tools (`tools/applications.py`, `tools/files.py`).
- Audio input/output device and webcam enumeration (`devices/`).
- Initial Tkinter chat and status window (`ui/main_window.py`).
- Comprehensive Pytest test suite covering core components.
