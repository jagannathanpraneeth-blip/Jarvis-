"""
JARVIS — Main Entry Point

Phase 1: Text-only CLI chat loop.
Loads config, initializes the brain, and runs an interactive conversation.
"""

from __future__ import annotations

import argparse
import sys

from core.config import load_settings
from core.logger import setup_logging, get_logger
from core.brain import Brain
from memory.buffer import ConversationBuffer
from core.voice_loop import VoiceLoop
import threading
import multiprocessing

from ui.tray import TrayApp
from ui.dashboard import serve as serve_dashboard
from ui.hud import run_hud
from core.scheduler import JARVISScheduler
from core.startup import ensure_startup


def print_banner(assistant_name: str, user_name: str) -> None:
    """Print the JARVIS startup banner."""
    print()
    print("=" * 56)
    print(f"  {assistant_name} — Personal AI Assistant")
    print("=" * 56)
    print(f"  Good day, {user_name}. How may I assist you?")
    print(f"  Type 'quit' or 'exit' to end the session.")
    print(f"  Type 'clear' to reset conversation history.")
    print("=" * 56)
    print()


def parse_args():
    parser = argparse.ArgumentParser(description="JARVIS Personal Assistant")
    parser.add_argument("--voice", action="store_true", help="Start in voice mode")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # ── Load configuration ──
    settings = load_settings()
    settings.validate()

    # ── Initialize logging ──
    setup_logging(
        level=settings.logging.level,
        log_to_file=settings.logging.log_to_file,
        log_dir=settings.log_dir_path,
    )
    logger = get_logger("main")
    logger.info(f"{settings.assistant_name} starting up...")

    # ── Initialize brain and memory ──
    brain = Brain(settings)
    buffer = ConversationBuffer(max_turns=settings.memory.buffer_size)

    # Inject JARVIS into Windows startup sequence (Phase 9)
    ensure_startup()

    logger.info("All systems online.")
    
    # ── Start UI Components (Phase 7 & 8) ──
    logger.info("Starting UI components and background processes...")
    
    # 1. System Tray
    tray = TrayApp(settings)
    tray.start()
    
    # 2. Web Dashboard
    dashboard_thread = threading.Thread(
        target=serve_dashboard, 
        args=(settings, brain, buffer), 
        daemon=True
    )
    dashboard_thread.start()
    
    # 3. HUD Overlay (Multiprocessing)
    hud_process = multiprocessing.Process(target=run_hud, daemon=True)
    hud_process.start()
    
    # 4. Proactive Scheduler
    scheduler = JARVISScheduler(settings, brain, buffer)
    scheduler.start()
    
    print_banner(settings.assistant_name, settings.user_name)

    if args.voice:
        logger.info("Starting JARVIS in VOICE mode")
        try:
            loop = VoiceLoop(settings, brain, buffer)
            threading.Thread(target=loop.start, daemon=True).start()
        except Exception as e:
            logger.error(f"Voice loop error: {e}", exc_info=True)

    logger.info("Starting Desktop GUI...")
    # Give the web server a moment to spin up
    import time; time.sleep(1)
    
    try:
        import webview
        # Create the native window pointing to the local dashboard
        window = webview.create_window(
            "J.A.R.V.I.S.", 
            "http://127.0.0.1:8000/", 
            frameless=True,
            transparent=True,
            width=1200, 
            height=800
        )
        # Start the webview loop (this blocks until the window is closed)
        webview.start()
    except Exception as e:
        logger.error(f"Failed to start GUI: {e}")
        # Fallback to text mode if GUI fails
        try:
            while True:
                user_input = input(f"  {settings.user_name} > ").strip()
                if not user_input: continue
                if user_input.lower() in ("quit", "exit"): break
                response = brain.think(user_input, buffer.get_history())
                buffer.add("user", user_input); buffer.add("assistant", response)
                print(f"\n  {settings.assistant_name}: {response}\n")
        except KeyboardInterrupt:
            pass

    logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
