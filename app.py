"""
app.py -- ZYRO desktop entry point.

Usage:
    python app.py                UI + voice agent (integrated default)
    python app.py --setup        Interactive First-Run Configuration Wizard
    python app.py --mode voice   full voice pipeline, no window
    python app.py --mode text    console dev mode (needs GEMINI_API_KEY, no mic)
    python app.py --mode ui      Tkinter status window only (no Live session)
    python app.py --mode status  prints config + tool list
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Fix garbled Unicode on Windows terminals that default to cp1252.
if hasattr(sys.stdout, "reconfigure") and sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure") and sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import CONFIG
from core.agent import ZyroAgent

logger = logging.getLogger("zyro")


def _print_status(agent: ZyroAgent) -> None:
    print(f"{agent.config.zyro_name} - Windows Voice AI Agent")
    print(f"  model:      {agent.config.gemini_model}")
    print(f"  mock mode:  {agent.config.mock_mode}")
    print(f"  api key:    {'set' if agent.config.gemini_api_key else 'NOT SET'}")
    print(f"  tools ({len(agent.registry.all())}):")
    for tool in agent.registry.all():
        print(f"    - {tool.name} [{tool.permission.value}] -- {tool.description}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ZYRO - Windows-first personal voice AI agent")
    parser.add_argument(
        "--mode",
        choices=["app", "status", "voice", "text", "ui"],
        default="app",
        help="app (default): UI + voice. status/voice/text/ui remain available for development.",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Launch the interactive First-Run Setup Wizard.",
    )
    args = parser.parse_args()

    # If --setup requested, launch wizard directly
    if args.setup:
        from ui.setup_wizard import ZyroSetupWizard
        wizard = ZyroSetupWizard()
        wizard.run()
        return

    # Check if first-run setup is required
    # (No API key set and not in mock mode, or .env missing)
    if args.mode in ("app", "ui") and not CONFIG.gemini_api_key and not CONFIG.mock_mode:
        from ui.setup_wizard import ZyroSetupWizard
        wizard = ZyroSetupWizard()
        wizard.run()
        # Reload configuration after setup completes
        from importlib import reload
        import config
        reload(config)

    agent = ZyroAgent(CONFIG)

    if args.mode == "status":
        _print_status(agent)
    elif args.mode == "voice":
        asyncio.run(agent.run_voice())
    elif args.mode == "text":
        asyncio.run(agent.run_text())
    elif args.mode == "ui":
        from ui.main_window import launch_ui
        launch_ui(agent, start_voice=False)
    elif args.mode == "app":
        from ui.main_window import launch_ui
        launch_ui(agent, start_voice=True)


if __name__ == "__main__":
    main()
