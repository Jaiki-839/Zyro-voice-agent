# ⚡ ZYRO — Features & Upcoming Roadmap

<p align="center">
  <img src="assets/zyro.png" alt="ZYRO Logo" width="100" height="100" />
</p>

Welcome to the **ZYRO Feature Guide & Future Roadmap**. This document highlights what ZYRO can do today on the desktop, and unveils the upcoming **ZYRO Mobile for Android (Gemini-Powered)** ecosystem.

---

## 🌟 Current Production Features (v1.0 Desktop)

### 1. True Standalone Windows Desktop Client
- **Zero Terminal / No VS Code**: Runs natively via windowed GUI (`zyro_app.pyw`, `launch_zyro.bat`, `run_silent.vbs`, or compiled `dist/ZYRO/ZYRO.exe`).
- **Cyber-Obsidian Modern UI**: High-contrast, dark slate theme with glowing cyber-emerald (`#10B981`) and electric cyan (`#06B6D4`) accents.
- **Dynamic Waveform Visualizer**: Smooth soundwave canvas rendering real-time audio vibrations during active speech and listening.
- **Quick-Action Chips Ribbon**: Instant one-click triggers for Web Search, Spotify, WhatsApp Web, File Search, and Sleep/Wake toggles.
- **Guided First-Run Setup Wizard**: Intuitive 3-step setup with one-click Google AI Studio API key acquisition and live connection verification.

### 2. Autonomous Gemini Live Streaming Engine
- **Sub-Second Voice Latency**: Bi-directional full-duplex PortAudio (16 kHz capture, 24 kHz playback) streaming over persistent WebSockets.
- **Interruption Handling**: Instant speech interruption support — stop ZYRO mid-sentence simply by speaking.
- **Adaptive Voice Activity Detection**: Filters background noise and manages speech boundaries automatically.

### 3. Desktop, System & Web Automation (30+ Tools)
- **Windows OS Control**: Launch applications, close windows, cycle tasks (`Alt+Tab`), minimize/maximize, manage virtual browser tabs.
- **Global Media Integration**: Control Windows master volume, play/pause, next/previous tracks on Spotify and web players.
- **Web App Navigation**: Native browser tab automation for WhatsApp Web (search contacts & send messages), Discord (switch channels & servers), YouTube, and Instagram.
- **Local File Search**: Blazing-fast file indexing across user directories (`Desktop`, `Documents`, `Downloads`, `Music`, `Videos`).

### 4. 100% Privacy & Sovereign Local Memory
- **Persistent SQLite Knowledge Base**: Stores user details, facts, reminders, and preferences locally in `data/zyro_memory.db`.
- **Zero Telemetry / No Tracking Servers**: Voice streams go directly to Google's official Gemini endpoint. Local logs (`zyro.log`) stay strictly on your device.
- **Safe Sandboxed Mock Mode**: Simulate all OS actions safely without executing real system modifications.

---

## 📱 Upcoming Release: ZYRO Mobile for Android (Gemini-Powered)

> **"Take ZYRO anywhere in your pocket — powered by Google Gemini multimodal intelligence."**

We are actively engineering **ZYRO for Android** to bring the sovereign, autonomous voice assistant experience to mobile smartphones.

```text
 ┌────────────────────────────────────────────────────────┐
 │            ZYRO Mobile for Android (Vision)            │
 ├────────────────────────────────────────────────────────┤
 │                                                        │
 │   📱 Floating Voice Widget & Dynamic Island Pill       │
 │   🗣️ Continuous Gemini Live Full-Duplex Voice          │
 │   👁️ Gemini Vision: Point Camera & Ask ZYRO           │
 │   💬 WhatsApp, Phone Calls, SMS & Alarms Hands-Free    │
 │   🔄 Cross-Device Sync with ZYRO Desktop (Local Wi-Fi) │
 │                                                        │
 └────────────────────────────────────────────────────────┘
```

### 🎯 Key Highlights of the Android Version:

#### 1. Gemini-Powered Conversational Intelligence
- **Google Gemini 2.5 / 3.8 Multimodal Core**: Natural, empathetic, human-like voice conversations right from your smartphone.
- **Gemini Nano On-Device Fallback**: Basic offline commands (alarms, timers, local apps, flashlight) run locally on-device without an active internet connection.
- **Bilingual & Hinglish Fluency**: Seamlessly understand and speak English, Hindi, and natural Hinglish code-switching with native accent adaptation.

#### 2. Android System-Level Voice Control
- **Hands-Free Phone Calls & SMS**: *"Call Alex on speaker"* or *"Text Mom that I'll be home in 10 minutes"*.
- **Automated WhatsApp Messaging**: Native Android accessibility automation to search contacts and dispatch WhatsApp messages without opening the screen.
- **Smart Phone Utilities**: Set alarms, toggle Wi-Fi / Bluetooth / Hotspot, adjust screen brightness, turn on flashlight, and set Google Calendar reminders.

#### 3. Real-Time Camera Vision (Gemini Multimodal)
- **"ZYRO, what am I looking at?"**: Use your phone's camera in real time to ask questions about physical objects, solve handwritten math problems, read road signs in foreign languages, or diagnose engine parts.
- **Visual Document Summarization**: Point your phone camera at a physical printed document, lease, or receipt and have ZYRO summarize key clauses aloud.

#### 4. Floating Overlay & Ambient Mode
- **Dynamic Voice Island / Floating Pill**: A non-intrusive floating voice bubble that appears on top of any Android app when you summon ZYRO.
- **Lock Screen & Always-On Wake Word**: Optional low-power wake word detection (*"Hey ZYRO"*) even when the phone display is off.

#### 5. Cross-Device Ecosystem Sync (Desktop ⇄ Android)
- **Shared Memory Knowledge Base**: Facts remembered on your PC (*"My WiFi password is..."*) are immediately accessible on your phone via end-to-end encrypted local Wi-Fi synchronization.
- **Remote Desktop Actions**: Tell your Android phone: *"ZYRO, open my budget spreadsheet on my PC and start my Spotify playlist"* — and watch your desktop obey!

---

## 🗺️ Engineering Roadmap

| Quarter | Milestone | Focus Area | Status |
| ------- | --------- | ---------- | ------ |
| **Q3 2026** | **v0.1 – v0.4 Prototype** | PortAudio pipeline, Gemini Live WebSocket client, initial tool dispatcher, Tkinter UI. | ✅ Completed |
| **Q4 2026** | **v1.0 Desktop Release** | Standalone .exe, Cyber-Obsidian UI, animated visualizer, setup wizard, Word .docx suite, installer. | ✅ Completed |
| **Q1 2027** | **v1.5 Screen Awareness** | Desktop screen capture stream to Gemini Vision for real-time visual assistance. | 🚧 In Progress |
| **Q2 2027** | **v2.0 ZYRO Android Alpha** | Kotlin Android app, Gemini Live mobile client, system call/SMS tools, floating UI. | 📅 Planned |
| **Q3 2027** | **v2.5 Cross-Device Sync** | Local peer-to-peer encrypted memory sync between Windows Desktop and Android phone. | 📅 Planned |

---

## 💡 Suggest a Feature

Have an idea for a cool desktop tool or Android feature?
- Open a feature suggestion under [GitHub Issues](https://github.com/zyro-ai/zyro/issues).
- Check out [`CONTRIBUTING.md`](CONTRIBUTING.md) to build and submit your own tools to the project!
