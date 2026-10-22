# ZYRO — Autonomous Windows Desktop Voice AI Assistant

<p align="center">
  <img src="assets/zyro.png" alt="ZYRO Logo" width="130" height="130" />
</p>

<p align="center">
  <b>A Windows-first, privacy-focused autonomous voice AI agent powered by Google Gemini Live.</b><br>
  Runs as a standalone desktop application with zero terminal, command prompt, or VS Code required.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-10B981.svg" alt="License: MIT"></a>
  <a href="https://microsoft.com/windows"><img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-06B6D4.svg" alt="Platform: Windows"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3B82F6.svg" alt="Python"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-409%20Passed-10B981.svg" alt="Tests"></a>
  <a href="docs/"><img src="https://img.shields.io/badge/Docs-5x%20Word%20.docx%20Suite-8B5CF6.svg" alt="Word Docs"></a>
  <a href="FEATURES.md"><img src="https://img.shields.io/badge/Roadmap-Android%20%26%20Vision-FF6F61.svg" alt="Android Roadmap"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/Version-v1.0.0-F59E0B.svg" alt="Version"></a>
</p>

---

## Table of Contents

1. [Overview](#-overview)
2. [Key Features & Upcoming Android Release](#-key-features)
   - [Full Features & Android Roadmap Guide (FEATURES.md)](FEATURES.md)
3. [End-to-End Privacy & Local Security Architecture](#-end-to-end-privacy--local-security-architecture)
4. [System Architecture](#-system-architecture)
5. [Installation & Setup](#-installation--setup)
   - [Method 1: One-Click Desktop Installer (Recommended)](#method-1-one-click-desktop-installer-recommended)
   - [Method 2: Standalone Portable ZIP](#method-2-standalone-portable-zip)
   - [Method 3: Developer Setup from Source](#method-3-developer-setup-from-source)
6. [Voice Commands Reference](#-voice-commands-reference)
7. [In-App Settings & First-Run Wizard](#-in-app-settings--first-run-wizard)
8. [Microsoft Word (.docx) Documentation Suite](#-microsoft-word-docx-documentation-suite)
9. [Building Standalone .exe from Source](#-building-standalone-exe-from-source)
10. [Authors, Contributors & Attribution](#-authors-contributors--attribution)
11. [How to Push & Create a GitHub Release](#-how-to-push--create-a-github-release)
12. [License](#-license)

---

## 🌟 Overview

**ZYRO** is an open-source, full-duplex voice artificial intelligence agent built specifically for the Windows desktop ecosystem. By leveraging Google's **Gemini Live Multimodal API** over persistent WebSockets combined with local **PortAudio streaming**, ZYRO offers natural, low-latency conversational AI capable of interacting with your operating system in real-time.

Unlike cloud-bound web chatbots, ZYRO can launch and manage desktop applications, control windows, manipulate media playback, automate browser tabs (WhatsApp Web, Discord, Spotify, YouTube), index and open local files, and retain persistent personal memories across conversations.

---

## ✨ Key Features

- **True Desktop Experience**: Runs as a native desktop application with no CMD prompt or terminal popping up. Includes `.pyw`, `.bat`, `.vbs`, and compiled `.exe` launchers.
- **Cyber Obsidian Dark UI**: Ultra-clean desktop interface styled with deep obsidian slate (`#0B0F19`), cyber emerald (`#10B981`), and electric cyan (`#06B6D4`).
- **Real-Time Animated Waveform Visualizer**: Smooth soundwave canvas that dynamically pulses and reacts to voice states: *Listening*, *Speaking*, *Thinking*, and *Sleeping*.
- **Quick-Action Chips Ribbon**: One-click quick actions for Web Search, Spotify playback, WhatsApp messaging, Document search, and Sleep/Wake toggling.
- **Interactive First-Run Wizard & Settings**: Integrated graphical wizard to configure and live-verify your Gemini API key with Google GenAI with a single click.
- **Autonomous Tool Dispatcher**: 30+ registered system tools protected by a 3-tier permission model (`READ_ONLY`, `USER_ACTION`, `SYSTEM_WRITE`).
- **Persistent SQLite Memory**: Stores user preferences, facts, and notes locally in an indexed SQLite database with recency-weighted recall.
- **Safe Mock Mode**: Fully sandboxed simulation mode (`ZYRO_MOCK_MODE=true`) allowing complete end-to-end testing without making real system or filesystem modifications.

---

## 🔒 End-to-End Privacy & Local Security Architecture

Privacy and user sovereignty are foundational pillars of ZYRO:

| Privacy Guarantee | Implementation Detail |
| ----------------- | --------------------- |
| **100% Local Execution** | ZYRO runs exclusively on the user's host PC. There are **no central tracking servers**, no telemetry relays, and no third-party data analytics. |
| **Zero Shared Logs** | Every user's `zyro.log` is generated locally in their private install directory (`%LOCALAPPDATA%\Programs\ZYRO\zyro.log`). Logs are never transmitted over the network and are strictly ignored in `.gitignore`. |
| **Direct API Connection** | Audio packets and text streams travel directly from your machine to Google's official Gemini Live endpoint over encrypted TLS WebSockets. |
| **Local Knowledge Base** | Memories, user identity, and preference vectors are stored in a local SQLite file on your machine (`data/zyro_memory.db`). Your personal data is never uploaded to external databases. |
| **Explicit Permission Tiers** | System-altering tools (`SYSTEM_WRITE`) require authorization and are completely disabled in Mock Mode to prevent accidental modifications. |
| **Microphone & Camera Privacy** | The webcam is **OFF by default** and only initialized if explicitly requested. Microphone input is gated by an adaptive noise threshold and voice activity detector. |

---

## 🏛️ System Architecture

```text
  ┌──────────────────────────────────────────────────────────────┐
  │                 Windows User / Microphone                   │
  └──────────────────────────────┬───────────────────────────────┘
                                 │ (16 kHz PCM Mono Audio Stream)
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │               Full-Duplex PortAudio Pipeline                 │
  │   - Adaptive Noise Gate      - Asynchronous Ring Buffer     │
  └──────────────────────────────┬───────────────────────────────┘
                                 │ (Base64 PCM Chunks / WebSocket)
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │              Google Gemini Live Multimodal API               │
  │      - gemini-3.8-live / gemini-2.5-flash Engine             │
  │      - Bi-directional Streaming & Turn Interruption          │
  └──────────────────────────────┬───────────────────────────────┘
                                 │ (ToolCall JSON Payload)
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                 ZYRO Core Dispatcher Layer                   │
  │   - Security & Permission Gate (READ_ONLY / USER / SYSTEM)   │
  │   - Safe Mock Mode Interceptor                               │
  └──────────────────────────────┬───────────────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
  ┌─────────────────────────────┐         ┌─────────────────────────────┐
  │   Local Windows OS Tools    │         │    Browser WebApp Layer     │
  │  - App Launcher & Focus     │         │  - WhatsApp Web Automation  │
  │  - Window Management        │         │  - Discord Server Nav       │
  │  - Media Play / Pause / Vol │         │  - Spotify & YouTube Player │
  │  - File Search & Open       │         │  - Web Search & Scraper     │
  │  - SQLite Persistent Memory │         │  - Instagram Profiles       │
  └─────────────────────────────┘         └─────────────────────────────┘
                                 │ (Execution Result JSON)
                                 ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                   Native Speaker Playback                    │
  │   - 24 kHz High-Definition Audio Buffer                      │
  │   - Real-time Waveform Canvas in Desktop UI                  │
  └──────────────────────────────────────────────────────────────┘
```

---

## 📥 Installation & Setup

### Method 1: One-Click Desktop Installer (Recommended)

1. Download the ZYRO release folder or archive.
2. In the folder, double-click **`launch_installer.bat`** (or run `installer/setup_zyro.py`).
3. The graphical setup wizard will open:
   - Select your installation folder (defaults to `%LOCALAPPDATA%\Programs\ZYRO`).
   - Paste your **Gemini API Key** (or check *Mock Mode* for free offline testing).
   - Check **Create Desktop Shortcut** and **Create Start Menu Shortcut**.
   - Click **Install ZYRO Now**.
4. ZYRO will automatically install, place an icon on your desktop, and launch! Next time, simply double-click the **ZYRO Voice Agent** shortcut on your desktop.

---

### Method 2: Standalone Portable ZIP

1. Download **`ZYRO_v1.0.0_Windows_x64_Portable.zip`** from [GitHub Releases](https://github.com/zyro-ai/zyro/releases).
2. Extract the ZIP archive anywhere on your PC (e.g., `C:\ZYRO` or `Desktop\ZYRO`).
3. Double-click **`ZYRO.exe`** inside the folder.
4. If it is your first time, the guided **First-Run Wizard** will appear to configure your API key and microphone.

---

### Method 3: Developer Setup from Source

If you want to modify code, add custom tools, or run unit tests:

```powershell
# 1. Clone repository
git clone https://github.com/zyro-ai/zyro.git
cd zyro

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run Desktop GUI + Voice Assistant
python app.py

# 5. (Optional) Run unit test suite
pytest
```

---

## 🎙️ Voice Commands Reference

ZYRO understands natural speech. Below are examples of supported commands:

### Desktop & Window Controls
| Voice Command | Action Taken by ZYRO |
| ------------- | -------------------- |
| *"Open Google Chrome"* / *"Open Notepad"* | Launches registered Windows application |
| *"Close Notepad"* / *"Close active window"* | Closes target window safely |
| *"Switch application"* / *"Next window"* | Cycles between active windows (`Alt+Tab`) |
| *"Maximize window"* / *"Minimize window"* | Resizes target application window |
| *"Next tab"* / *"Close tab"* | Controls active browser tabs |

### Media & Audio Controls
| Voice Command | Action Taken by ZYRO |
| ------------- | -------------------- |
| *"Play Bohemian Rhapsody on Spotify"* | Opens Spotify and plays query |
| *"Pause music"* / *"Play music"* | Toggles global Windows media playback |
| *"Next song"* / *"Previous track"* | Skips or rewinds media track |
| *"Volume up"* / *"Volume down"* / *"Mute"* | Adjusts master Windows audio volume |

### Web & Messaging Automation
| Voice Command | Action Taken by ZYRO |
| ------------- | -------------------- |
| *"Search the web for James Webb telescope discoveries"* | Queries web and synthesizes clean summary |
| *"Open WhatsApp"* / *"Search John on WhatsApp"* | Automates WhatsApp Web contact selection |
| *"Send message to Alex on WhatsApp saying I'm on my way"* | Types and delivers WhatsApp message |
| *"Open Discord"* / *"Open general channel"* | Navigates Discord channels and servers |
| *"Open YouTube and search lo-fi hip hop"* | Launches YouTube video search |

### Memory & Personal Assistant
| Voice Command | Action Taken by ZYRO |
| ------------- | -------------------- |
| *"Remember that my car registration is ABC-1234"* | Stores key-value fact into local SQLite database |
| *"Recall my car registration"* | Retrieves saved memory instantly |
| *"Hey ZYRO, go to sleep"* | Pauses audio capture to preserve privacy |
| *"Hey ZYRO, wake up"* | Resumes active conversational listening |

---

## ⚙️ In-App Settings & First-Run Wizard

ZYRO includes an interactive desktop configuration dialog:

- **Gemini API Configuration**: Paste your API key, toggle visibility, and click **"⚡ Test Connection"** to verify API connectivity against Google GenAI in real time.
- **Model Selector**: Switch between `gemini-3.8-live`, `gemini-2.5-flash`, `gemini-2.0-flash`, or `gemini-1.5-pro`.
- **Personality & Identity**: Set your preferred name, greeting style, agent name, and custom persona prompt.
- **Search Roots Manager**: Add or remove folders indexed for local file search commands using a standard Windows folder browser.
- **Audio Hardware**: Select custom input microphones and output speakers with live playback test chimes.

---

## 📄 Microsoft Word (.docx) Documentation Suite

The [`docs/`](docs/) directory contains 5 comprehensive Microsoft Word manuals:

| Document | File Path | Focus Area |
| -------- | --------- | ---------- |
| **Architecture & Technical Specification** | [`docs/ZYRO_Architecture_and_Technical_Specification.docx`](docs/ZYRO_Architecture_and_Technical_Specification.docx) | In-depth engineering blueprint, PortAudio stream specifications, WebSocket protocol, and dispatcher security. |
| **User Guide & Desktop Manual** | [`docs/ZYRO_User_Guide_and_Desktop_Manual.docx`](docs/ZYRO_User_Guide_and_Desktop_Manual.docx) | End-user manual, step-by-step setup, UI walkthrough, and exhaustive voice command reference. |
| **Setup & Deployment Guide** | [`docs/ZYRO_Setup_and_Deployment_Guide.docx`](docs/ZYRO_Setup_and_Deployment_Guide.docx) | System requirements, API key generation, graphical installer walkthrough, and standalone build guide. |
| **Open Source Contributor Guide** | [`docs/ZYRO_Open_Source_Contributor_Guide.docx`](docs/ZYRO_Open_Source_Contributor_Guide.docx) | Code tour, adding new tools in 5 minutes, pytest conventions, and Git Conventional Commits standard. |
| **API & Tools Complete Reference** | [`docs/ZYRO_API_and_Tools_Reference.docx`](docs/ZYRO_API_and_Tools_Reference.docx) | Exhaustive parameter definitions, permission tiers, and JSON schemas for all 30+ registered tools. |

*To regenerate all Word documents at any time:*
```powershell
python docs/generate_docx_suite.py
```

---

## 🔨 Building Standalone .exe from Source

You can build the production Windows executable with a single command:

```powershell
# Compiles dist/ZYRO/ZYRO.exe
python build_exe.py

# Packages dist/ZYRO_v1.0.0_Windows_x64_Portable.zip
python package_release.py
```

---

## 👥 Authors, Contributors & Attribution

ZYRO was conceptualized, engineered, and open-sourced to deliver a truly sovereign, privacy-respecting Windows voice assistant:

- **Lead Architecture & Development**: ZYRO Core Engineering Team & Open Source Community Contributors.
- **Core LLM Technology**: Built on Google DeepMind's Gemini Multimodal Live API.
- **Audio & System Engineering**: Powered by PortAudio (`sounddevice`), PyAudio, and Windows Win32 API.
- **Community**: Contributions, issue reports, and tool additions are warmly welcomed by developers worldwide.

---

## 🚀 How to Push & Create a GitHub Release

Follow these quick steps to push this codebase to GitHub and publish the installer:

### 1. Push to Your GitHub Repository
```powershell
# Rename branch to main
git branch -M main

# Link your GitHub repository (replace with your username and repo)
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/zyro.git

# Push all commits and code
git push -u origin main
```

### 2. Create the GitHub Release
1. Open your repository on GitHub and navigate to **Releases** (right sidebar) ➔ Click **Create a new release**.
2. Set Tag version: `v1.0.0`.
3. Set Release title: `ZYRO Voice Agent v1.0.0 — Standalone Desktop Release`.
4. Copy the release notes from [`CHANGELOG.md`](CHANGELOG.md).
5. Drag and drop the portable package into the release binaries area:
   - `dist/ZYRO_v1.0.0_Windows_x64_Portable.zip`
6. Click **Publish release**.

Anyone around the world can now download ZYRO, extract the package, and enjoy a full desktop voice assistant with a single click!

---

## 📜 License

This project is open-source software licensed under the **[MIT License](LICENSE)**.
Free for personal, academic, and commercial use.
