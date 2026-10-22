"""
docs/generate_docx_suite.py -- Generates professional Microsoft Word (.docx)
technical manuals and guides for the ZYRO Desktop Voice Agent project.
"""
from __future__ import annotations

import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = Path(__file__).resolve().parent

# Color Palette
CLR_PRIMARY = RGBColor(11, 17, 32)      # Deep Obsidian #0B1120
CLR_ACCENT = RGBColor(16, 185, 129)     # Emerald Green #10B981
CLR_SECONDARY = RGBColor(6, 182, 212)   # Cyan #06B6D4
CLR_SLATE = RGBColor(71, 85, 105)       # Slate Gray #475569
CLR_MUTED = RGBColor(148, 163, 184)     # Muted #94A3B8

HEX_CARD_BG = "F8FAFC"
HEX_HEADER_BG = "0B1120"
HEX_HEADER_FG = "FFFFFF"
HEX_BORDER = "CBD5E1"
HEX_CALLOUT_BG = "ECFDF5"
HEX_CALLOUT_BORDER = "10B981"


def set_cell_background(cell, hex_color: str) -> None:
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=140, bottom=140, left=180, right=180) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_callout(doc: Document, text: str, title: str = "NOTE") -> None:
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, HEX_CALLOUT_BG)
    set_cell_margins(cell, top=140, bottom=140, left=220, right=200)

    # Left border only (accent emerald)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{HEX_CALLOUT_BORDER}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    run_t = p.add_run(f"[{title}] ")
    run_t.bold = True
    run_t.font.name = "Segoe UI"
    run_t.font.size = Pt(9.5)
    run_t.font.color.rgb = CLR_ACCENT

    run_b = p.add_run(text)
    run_b.font.name = "Segoe UI"
    run_b.font.size = Pt(9.5)
    run_b.font.color.rgb = CLR_SLATE
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def format_table(tbl, col_widths: list[float]) -> None:
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    # Header row formatting
    hdr = tbl.rows[0]
    for idx, cell in enumerate(hdr.cells):
        set_cell_background(cell, HEX_HEADER_BG)
        set_cell_margins(cell, top=140, bottom=140, left=160, right=160)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.font.bold = True
            run.font.name = "Segoe UI Semibold"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(255, 255, 255)

    # Data rows
    for r_idx, row in enumerate(tbl.rows[1:], start=1):
        bg = HEX_CARD_BG if r_idx % 2 == 1 else "FFFFFF"
        for idx, cell in enumerate(row.cells):
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            p = cell.paragraphs[0]
            for run in p.runs:
                run.font.name = "Segoe UI"
                run.font.size = Pt(9)
                run.font.color.rgb = CLR_PRIMARY

    # Apply widths
    for row in tbl.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = Inches(width)


def create_cover(doc: Document, title: str, subtitle: str, doc_type: str, version: str = "v1.0.0") -> None:
    # Top spacing
    p_top = doc.add_paragraph()
    p_top.paragraph_format.space_before = Pt(36)
    p_top.paragraph_format.space_after = Pt(12)

    # Badge pill
    p_badge = doc.add_paragraph()
    run_badge = p_badge.add_run(f" ZYRO OPEN SOURCE PROJECT  •  {doc_type.upper()} ")
    run_badge.font.name = "Segoe UI Semibold"
    run_badge.font.size = Pt(9)
    run_badge.font.color.rgb = CLR_ACCENT
    run_badge.bold = True
    p_badge.paragraph_format.space_after = Pt(18)

    # Title
    p_title = doc.add_paragraph()
    run_title = p_title.add_run(title)
    run_title.font.name = "Segoe UI"
    run_title.font.size = Pt(28)
    run_title.bold = True
    run_title.font.color.rgb = CLR_PRIMARY
    p_title.paragraph_format.space_after = Pt(10)

    # Subtitle
    p_sub = doc.add_paragraph()
    run_sub = p_sub.add_run(subtitle)
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = CLR_SLATE
    p_sub.paragraph_format.space_after = Pt(24)

    # Divider bar
    p_div = doc.add_paragraph()
    run_div = p_div.add_run("―" * 48)
    run_div.font.color.rgb = CLR_ACCENT
    p_div.paragraph_format.space_after = Pt(28)

    # Metadata table
    tbl = doc.add_table(rows=4, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    meta = [
        ("Document Version:", f"{version} (Production Desktop Release)"),
        ("Author / Organization:", "ZYRO Open Source Engineering Team"),
        ("Target Platform:", "Windows 10 / Windows 11 (x64)"),
        ("Core LLM Backbone:", "Google Gemini 3.8 / 2.5 Live Multimodal"),
    ]
    for idx, (k, v) in enumerate(meta):
        c0 = tbl.cell(idx, 0)
        c1 = tbl.cell(idx, 1)
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.bold = True
        r0.font.name = "Segoe UI Semibold"
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = CLR_PRIMARY
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.name = "Segoe UI"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = CLR_SLATE

    doc.add_page_break()


def add_heading_1(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Segoe UI"
    run.font.size = Pt(16)
    run.bold = True
    run.font.color.rgb = CLR_PRIMARY


def add_heading_2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Segoe UI Semibold"
    run.font.size = Pt(12)
    run.bold = True
    run.font.color.rgb = CLR_SLATE


def add_p(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = "Segoe UI"
    run.font.size = Pt(10)
    run.font.color.rgb = CLR_PRIMARY


def add_bullet(doc: Document, bold_prefix: str, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(bold_prefix + ": ")
    r1.bold = True
    r1.font.name = "Segoe UI Semibold"
    r1.font.size = Pt(9.5)
    r1.font.color.rgb = CLR_PRIMARY
    
    r2 = p.add_run(text)
    r2.font.name = "Segoe UI"
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = CLR_SLATE


# ==============================================================================
# DOC 1: Architecture & Technical Specification
# ==============================================================================
def generate_architecture_doc() -> Path:
    doc = Document()
    create_cover(
        doc,
        title="ZYRO Voice Agent\nArchitecture & Technical Specification",
        subtitle="Comprehensive Engineering Blueprint for the Standalone Windows-First Voice AI System",
        doc_type="Technical Specification",
    )

    add_heading_1(doc, "1. Executive Architecture Summary")
    add_p(doc, "ZYRO is a native Windows-first voice artificial intelligence agent designed to operate directly from the Windows desktop without requiring terminal environments, command prompts, or IDEs. It provides real-time, bi-directional audio streaming with sub-second latency powered by Google's Gemini Live multimodal API over persistent WebSockets.")
    add_p(doc, "The agent architecture is cleanly partitioned into asynchronous reactive layers: audio ingestion, WebSocket stream multiplexing, tool dispatching with three-tier permission enforcement, SQLite persistent user memory, OS desktop automation, and a Tkinter-based modern desktop graphical interface.")

    add_callout(doc, "ZYRO is engineered with strict mock safety. When ZYRO_MOCK_MODE=true is configured, every system-altering tool is simulated without executing destructive file or process mutations, allowing safe verification in any development environment.", "SAFETY DESIGN")

    add_heading_1(doc, "2. High-Level System Topology")
    add_p(doc, "The following table details the primary subsystems comprising the ZYRO desktop architecture:")

    tbl = doc.add_table(rows=7, cols=3)
    tbl.rows[0].cells[0].paragraphs[0].add_run("Subsystem")
    tbl.rows[0].cells[1].paragraphs[0].add_run("Implementation")
    tbl.rows[0].cells[2].paragraphs[0].add_run("Key Responsibility")

    subsystems = [
        ("Core Agent Controller", "core/agent.py, core/session.py", "Coordinates live loops, dispatching, and agent state transitions."),
        ("Voice Pipeline (I/O)", "audio/mic.py, audio/player.py", "Full-duplex PortAudio capture (16kHz PCM) and playback (24kHz PCM)."),
        ("Gemini Live Protocol", "gemini/client.py, gemini/live.py", "Bi-directional WebSocket streaming with Google GenAI SDK."),
        ("Tool Registry & Dispatcher", "core/tools.py, core/dispatcher.py", "Tool catalog with READ_ONLY, USER_ACTION, SYSTEM_WRITE permissions."),
        ("Memory Subsystem", "memory/sqlite_memory.py", "Persistent key-value knowledge base with keyword and recency search."),
        ("Desktop UI Engine", "ui/main_window.py, ui/theme.py", "Modern dark-themed Tkinter GUI, visualizer, and settings wizard."),
    ]
    for idx, (sub, impl, resp) in enumerate(subsystems, start=1):
        tbl.rows[idx].cells[0].paragraphs[0].add_run(sub)
        tbl.rows[idx].cells[1].paragraphs[0].add_run(impl)
        tbl.rows[idx].cells[2].paragraphs[0].add_run(resp)
    format_table(tbl, [1.8, 2.0, 2.7])

    add_heading_1(doc, "3. Real-Time Audio Streaming Pipeline")
    add_p(doc, "Audio ingestion is managed through PyAudio / PortAudio via sounddevice. The microphone capture loop records raw 16,000 Hz, 16-bit Mono PCM audio in chunks of 512 samples. Inactive silence is filtered with an adaptive noise gate, and active audio chunks are packaged as base64-encoded mime chunks (audio/pcm;rate=16000) sent upstream over the Gemini Live WebSocket session.")
    add_p(doc, "Playback receives raw 24,000 Hz PCM audio packets from Gemini Live chunks and buffers them into an asynchronous sounddevice.OutputStream. If the user interrupts or speaks mid-utterance, Gemini sends an interruption frame, and ZYRO instantly drains the output ring buffer to prevent speech overlap.")

    add_heading_1(doc, "4. Security & Permissions Architecture")
    add_p(doc, "ZYRO enforces a rigorous three-tiered permission security model to guarantee safe autonomous operation on user workstations:")
    add_bullet(doc, "READ_ONLY", "Safe queries with zero side effects (e.g. read_webpage, search_memory, list_camera_devices). Always permissible.")
    add_bullet(doc, "USER_ACTION", "Actions that interact with user software or media (e.g. open_spotify, media_play, open_whatsapp). Executes with feedback notification.")
    add_bullet(doc, "SYSTEM_WRITE", "Operations that modify files, registry, or launch system processes (e.g. create_file, open_application, run_terminal). Blocked in Mock Mode.")

    out_path = DOCS_DIR / "ZYRO_Architecture_and_Technical_Specification.docx"
    doc.save(out_path)
    print(f"Generated: {out_path}")
    return out_path


# ==============================================================================
# DOC 2: User Guide & Desktop Manual
# ==============================================================================
def generate_user_guide_doc() -> Path:
    doc = Document()
    create_cover(
        doc,
        title="ZYRO Desktop Voice Agent\nUser Guide & Operation Manual",
        subtitle="Complete Everyday Manual for Voice Commands, Desktop Navigation, and Configuration",
        doc_type="User Manual",
    )

    add_heading_1(doc, "1. Getting Started with ZYRO")
    add_p(doc, "Welcome to ZYRO! ZYRO is your personal desktop voice assistant for Windows. Unlike browser-only chatbots, ZYRO can see your files, control your desktop windows, search the web, play music, open apps, send WhatsApp messages, and remember personal facts across conversations.")
    
    add_heading_2(doc, "Launching the Desktop Application")
    add_p(doc, "You can start ZYRO in multiple ways without ever opening a command prompt:")
    add_bullet(doc, "Desktop Shortcut", "Double-click the 'ZYRO Voice Agent' shortcut on your Desktop.")
    add_bullet(doc, "Start Menu", "Open Start Menu and search for 'ZYRO'.")
    add_bullet(doc, "Direct Launcher", "Double-click 'launch_zyro.bat' or 'run_silent.vbs' in your ZYRO installation folder.")

    add_heading_1(doc, "2. User Interface Overview")
    add_p(doc, "The ZYRO desktop window is designed with an intuitive, modern dark theme:")
    add_bullet(doc, "Status Pill", "Shows current agent state: LIVE, LISTENING (Cyan), SPEAKING (Emerald), THINKING (Amber), or SLEEPING (Slate).")
    add_bullet(doc, "Audio Waveform Visualizer", "Dynamic audio bars at the top vibrate in real-time when ZYRO listens or speaks.")
    add_bullet(doc, "Device Ribbon", "Quick status of connected Microphone, Speaker, and Camera.")
    add_bullet(doc, "Quick Action Chips", "One-click shortcut chips (Web, Spotify, WhatsApp, Documents, Sleep, Clear Chat).")
    add_bullet(doc, "Chat Transcript", "Chronological chat history with avatars, timestamps, and tool execution status lines.")
    add_bullet(doc, "Message Composer", "Allows typing text commands when you cannot speak aloud.")

    add_heading_1(doc, "3. Voice Commands Reference")
    add_p(doc, "Speak naturally to ZYRO! Here are examples of commands recognized out of the box:")

    tbl = doc.add_table(rows=9, cols=3)
    tbl.rows[0].cells[0].paragraphs[0].add_run("Category")
    tbl.rows[0].cells[1].paragraphs[0].add_run("Example Voice Command")
    tbl.rows[0].cells[2].paragraphs[0].add_run("Agent Action")

    commands = [
        ("App Control", "'Open Google Chrome' / 'Close Notepad'", "Launches or closes Windows desktop applications."),
        ("Desktop Control", "'Maximize window' / 'Switch app' / 'Next tab'", "Manages active desktop windows and browser tabs."),
        ("Media & Music", "'Play Bohemian Rhapsody on Spotify' / 'Volume up'", "Controls Spotify or global Windows media playback."),
        ("Web & Search", "'Search the web for latest Mars rover discoveries'", "Searches DuckDuckGo/Google and summarizes results."),
        ("Files & Folders", "'Find budget report in Documents' / 'Open Downloads'", "Locates files across configured Windows search folders."),
        ("WhatsApp Web", "'Open WhatsApp' / 'Send message to Alex on WhatsApp'", "Automates WhatsApp Web contact search and messaging."),
        ("Memory & Recall", "'Remember that my dog's name is Milo' / 'Recall my dog'", "Saves and retrieves facts from SQLite user memory."),
        ("Sleep / Wake", "'Hey ZYRO, go to sleep' / 'Hey ZYRO, wake up'", "Toggles voice listening state to save battery and privacy."),
    ]
    for idx, (cat, cmd, act) in enumerate(commands, start=1):
        tbl.rows[idx].cells[0].paragraphs[0].add_run(cat)
        tbl.rows[idx].cells[1].paragraphs[0].add_run(cmd)
        tbl.rows[idx].cells[2].paragraphs[0].add_run(act)
    format_table(tbl, [1.6, 2.7, 2.2])

    add_heading_1(doc, "4. In-App Settings & Preferences")
    add_p(doc, "Click the '⚙ Settings & API' button in the bottom right corner of the window to open the full configuration dialog:")
    add_bullet(doc, "Gemini API Tab", "Change your Gemini API key, test key connection with one click, or toggle Mock Mode.")
    add_bullet(doc, "Identity Tab", "Change ZYRO's name, set your own preferred nickname, or customize the agent's personality.")
    add_bullet(doc, "Search Roots Tab", "Add or remove local Windows folders for file searches.")
    add_bullet(doc, "Devices Button", "Choose your preferred microphone and speaker from available Windows audio hardware.")

    out_path = DOCS_DIR / "ZYRO_User_Guide_and_Desktop_Manual.docx"
    doc.save(out_path)
    print(f"Generated: {out_path}")
    return out_path


# ==============================================================================
# DOC 3: Setup & Deployment Guide
# ==============================================================================
def generate_setup_guide_doc() -> Path:
    doc = Document()
    create_cover(
        doc,
        title="ZYRO Deployment Guide\nSetup, Packaging & Distribution",
        subtitle="Step-by-Step Instructions for Installation, API Setup, and Building Standalone Executables",
        doc_type="Deployment Guide",
    )

    add_heading_1(doc, "1. System Prerequisites")
    add_p(doc, "Before running or installing ZYRO, ensure your target machine meets these specifications:")
    add_bullet(doc, "Operating System", "Microsoft Windows 10 (Build 19041+) or Windows 11 (64-bit recommended).")
    add_bullet(doc, "Audio Hardware", "Working microphone and speakers/headphones.")
    add_bullet(doc, "Python (Source Only)", "Python 3.10 to 3.12 (if compiling or running from source code).")
    add_bullet(doc, "Internet Connection", "Required for Gemini Live API WebSocket stream (port 443).")

    add_heading_1(doc, "2. Obtaining a Gemini API Key")
    add_p(doc, "ZYRO requires a Gemini API key from Google AI Studio. Free-tier keys are fully supported:")
    add_bullet(doc, "Step 1", "Visit https://aistudio.google.com/app/apikey in your browser.")
    add_bullet(doc, "Step 2", "Sign in with your Google account and click 'Create API Key'.")
    add_bullet(doc, "Step 3", "Copy the generated key (starts with 'AIzaSy...').")
    add_bullet(doc, "Step 4", "Paste into ZYRO's Setup Wizard or Settings window and click 'Test Connection'.")

    add_heading_1(doc, "3. Installation Methods")
    add_heading_2(doc, "Method A: One-Click Windows Graphical Installer (Recommended for Users)")
    add_p(doc, "Run installer/setup_zyro.py or the compiled ZYRO_Setup.exe. The installer prompts for install directory, sets up your Gemini API key, creates Desktop and Start Menu shortcuts, and provides instant launch.")

    add_heading_2(doc, "Method B: Standalone Portable Package")
    add_p(doc, "Download ZYRO_v1.0.0_Windows_x64_Portable.zip, extract to any folder, and double-click ZYRO.exe. No python installation required.")

    add_heading_2(doc, "Method C: Developer Git Source Setup")
    add_p(doc, "Clone the repository, create a virtual environment, and install dependencies:")
    add_p(doc, "    git clone https://github.com/zyro-ai/zyro.git\n    cd zyro\n    python -m venv .venv\n    .\\.venv\\Scripts\\activate\n    pip install -r requirements.txt\n    python app.py")

    add_heading_1(doc, "4. Compiling the Standalone .exe (PyInstaller)")
    add_p(doc, "To compile ZYRO into a standalone Windows binary with zero console popup:")
    add_p(doc, "    python build_exe.py")
    add_p(doc, "This invokes zyro.spec, bundles icons, assets, and dependencies, and produces dist/ZYRO/ZYRO.exe.")

    out_path = DOCS_DIR / "ZYRO_Setup_and_Deployment_Guide.docx"
    doc.save(out_path)
    print(f"Generated: {out_path}")
    return out_path


# ==============================================================================
# DOC 4: Open Source Contributor Guide
# ==============================================================================
def generate_contributor_guide_doc() -> Path:
    doc = Document()
    create_cover(
        doc,
        title="ZYRO Open Source Project\nContributor & Developer Guide",
        subtitle="Architecture Conventions, Code Standards, Testing, and Contribution Guidelines",
        doc_type="Contributor Guide",
    )

    add_heading_1(doc, "1. Welcome Contributors")
    add_p(doc, "Thank you for contributing to ZYRO! ZYRO is an open-source project licensed under the MIT License. We welcome contributions from developers worldwide -- whether fixing bugs, adding tools, improving documentation, or refining UI design.")

    add_heading_1(doc, "2. Repository Layout")
    add_bullet(doc, "audio/", "Microphone capture, audio playback, ring buffers, and sounddevice adapters.")
    add_bullet(doc, "core/", "Agent loop, dispatcher, tool base classes, state manager, and permission model.")
    add_bullet(doc, "devices/", "Hardware device enumerators for audio input/output and webcams.")
    add_bullet(doc, "gemini/", "Gemini Live WebSockets client and stream packet handlers.")
    add_bullet(doc, "memory/", "SQLite persistent memory engine and recency ranking algorithms.")
    add_bullet(doc, "skills/", "High-level domain orchestration logic.")
    add_bullet(doc, "tools/", "Individual executable tool implementations (files, web, desktop, media, apps).")
    add_bullet(doc, "ui/", "Tkinter modern dark-mode interface, audio visualizer, settings dialog, setup wizard.")
    add_bullet(doc, "webapps/", "Browser automation adapters for WhatsApp, Discord, YouTube, Spotify.")
    add_bullet(doc, "tests/", "Full Pytest test suite with 400+ unit and integration tests.")

    add_heading_1(doc, "3. Adding a New Tool in 5 Minutes")
    add_p(doc, "Creating a new tool for ZYRO is simple and modular. Follow these steps:")
    add_bullet(doc, "Step 1", "Create or edit a module in tools/.")
    add_bullet(doc, "Step 2", "Define the tool function with type hints and a clear docstring.")
    add_bullet(doc, "Step 3", "Specify its PermissionLevel (READ_ONLY, USER_ACTION, or SYSTEM_WRITE).")
    add_bullet(doc, "Step 4", "Ensure the tool respects config.mock_mode if it modifies the filesystem or system.")
    add_bullet(doc, "Step 5", "Register the tool in core/agent.py.")
    add_bullet(doc, "Step 6", "Add unit tests in tests/ to verify mock and live behavior.")

    add_heading_1(doc, "4. Git Commit Standards")
    add_p(doc, "We adhere to Conventional Commits format:")
    add_bullet(doc, "feat", "New feature (e.g. feat(tools): add calculator tool)")
    add_bullet(doc, "fix", "Bug fix (e.g. fix(audio): resolve buffer underrun on playback)")
    add_bullet(doc, "docs", "Documentation updates (e.g. docs: update user manual)")
    add_bullet(doc, "test", "Adding or correcting tests (e.g. test(ui): verify dark mode)")

    out_path = DOCS_DIR / "ZYRO_Open_Source_Contributor_Guide.docx"
    doc.save(out_path)
    print(f"Generated: {out_path}")
    return out_path


# ==============================================================================
# DOC 5: API & Tools Reference
# ==============================================================================
def generate_api_reference_doc() -> Path:
    doc = Document()
    create_cover(
        doc,
        title="ZYRO Voice Agent\nAPI & Tools Complete Reference",
        subtitle="Exhaustive Specification of All Registered Tools, Permissions, and Return Formats",
        doc_type="API Reference",
    )

    add_heading_1(doc, "1. Tool Registry & Schema Overview")
    add_p(doc, "ZYRO provides over 30 specialized system tools registered dynamically into Google Gemini Live function declarations. Whenever Gemini decides to perform an action, it issues a ToolCall JSON payload which the ZYRO Dispatcher executes locally on Windows.")

    add_heading_1(doc, "2. Desktop & Window Management Tools")
    tbl = doc.add_table(rows=6, cols=3)
    tbl.rows[0].cells[0].paragraphs[0].add_run("Tool Name")
    tbl.rows[0].cells[1].paragraphs[0].add_run("Permission")
    tbl.rows[0].cells[2].paragraphs[0].add_run("Description")

    t_desktop = [
        ("open_application", "SYSTEM_WRITE", "Launches Windows application by executable name or Start Menu match."),
        ("close_window", "USER_ACTION", "Closes the active window or target window matching application title."),
        ("switch_app", "USER_ACTION", "Cycles to the next running desktop application (Alt+Tab)."),
        ("minimize_window", "USER_ACTION", "Minimizes active window or specified window to taskbar."),
        ("maximize_window", "USER_ACTION", "Maximizes target window to fill display."),
    ]
    for idx, (t, p, d) in enumerate(t_desktop, start=1):
        tbl.rows[idx].cells[0].paragraphs[0].add_run(t)
        tbl.rows[idx].cells[1].paragraphs[0].add_run(p)
        tbl.rows[idx].cells[2].paragraphs[0].add_run(d)
    format_table(tbl, [1.8, 1.4, 3.3])

    add_heading_1(doc, "3. Media & Audio Control Tools")
    tbl_m = doc.add_table(rows=6, cols=3)
    tbl_m.rows[0].cells[0].paragraphs[0].add_run("Tool Name")
    tbl_m.rows[0].cells[1].paragraphs[0].add_run("Permission")
    tbl_m.rows[0].cells[2].paragraphs[0].add_run("Description")

    t_media = [
        ("media_play_pause", "USER_ACTION", "Toggles system media play/pause via Windows virtual key codes."),
        ("media_next", "USER_ACTION", "Skips to the next track in current media player."),
        ("media_previous", "USER_ACTION", "Returns to previous track."),
        ("media_volume_up", "USER_ACTION", "Increases master Windows system volume by 4% increments."),
        ("media_mute", "USER_ACTION", "Mutes master audio output."),
    ]
    for idx, (t, p, d) in enumerate(t_media, start=1):
        tbl_m.rows[idx].cells[0].paragraphs[0].add_run(t)
        tbl_m.rows[idx].cells[1].paragraphs[0].add_run(p)
        tbl_m.rows[idx].cells[2].paragraphs[0].add_run(d)
    format_table(tbl_m, [1.8, 1.4, 3.3])

    add_heading_1(doc, "4. Web & Messaging Integration Tools")
    tbl_w = doc.add_table(rows=7, cols=3)
    tbl_w.rows[0].cells[0].paragraphs[0].add_run("Tool Name")
    tbl_w.rows[0].cells[1].paragraphs[0].add_run("Permission")
    tbl_w.rows[0].cells[2].paragraphs[0].add_run("Description")

    t_web = [
        ("web_search", "READ_ONLY", "Searches the web for queries and extracts top results."),
        ("open_url", "USER_ACTION", "Opens URL in user's default Windows web browser."),
        ("read_webpage", "READ_ONLY", "Fetches HTML content and extracts clean markdown/text."),
        ("open_whatsapp", "USER_ACTION", "Launches or focuses WhatsApp Web in browser."),
        ("send_whatsapp_message", "USER_ACTION", "Searches WhatsApp contact and transmits message text."),
        ("open_discord", "USER_ACTION", "Focuses Discord desktop client or web application."),
    ]
    for idx, (t, p, d) in enumerate(t_web, start=1):
        tbl_w.rows[idx].cells[0].paragraphs[0].add_run(t)
        tbl_w.rows[idx].cells[1].paragraphs[0].add_run(p)
        tbl_w.rows[idx].cells[2].paragraphs[0].add_run(d)
    format_table(tbl_w, [2.0, 1.4, 3.1])

    out_path = DOCS_DIR / "ZYRO_API_and_Tools_Reference.docx"
    doc.save(out_path)
    print(f"Generated: {out_path}")
    return out_path


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    print("==================================================")
    print("    Generating Complete ZYRO Word (.docx) Suite   ")
    print("==================================================")
    d1 = generate_architecture_doc()
    d2 = generate_user_guide_doc()
    d3 = generate_setup_guide_doc()
    d4 = generate_contributor_guide_doc()
    d5 = generate_api_reference_doc()
    print("==================================================")
    print("All 5 Microsoft Word (.docx) documents generated!")
    print(f"Location: {DOCS_DIR}")
    print("==================================================")


if __name__ == "__main__":
    main()
