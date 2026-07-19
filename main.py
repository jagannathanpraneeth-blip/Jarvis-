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

from ui.tray import TrayApp
from ui.dashboard import serve as serve_dashboard


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

    logger.info("All systems online.")
    
    # ── Start UI Components (Phase 7) ──
    logger.info("Starting UI components...")
    tray = TrayApp(settings)
    tray.start()
    
    dashboard_thread = threading.Thread(
        target=serve_dashboard, 
        args=(settings, brain), 
        daemon=True
    )
    dashboard_thread.start()
    
    print_banner(settings.assistant_name, settings.user_name)

    if args.voice:
        logger.info("Starting JARVIS in VOICE mode")
        try:
            loop = VoiceLoop(settings, brain)
            loop.start()
        except Exception as e:
            logger.error(f"Voice loop error: {e}", exc_info=True)
    else:
        logger.info("Entering text chat loop.")
        # ── Text Chat loop ──
        try:
            while True:
                try:
                    user_input = input(f"  {settings.user_name} > ").strip()
                except EOFError:
                    break
    
                if not user_input:
                    continue
    
                if user_input.lower() in ("quit", "exit"):
                    print(f"\n  {settings.assistant_name}: Until next time, {settings.user_name}.\n")
                    break
    
                if user_input.lower() == "clear":
                    buffer.clear()
                    print(f"  {settings.assistant_name}: Conversation history cleared.\n")
                    continue
    
                # Send to brain with conversation history
                logger.info(f"User: {user_input}")
                history = buffer.get_history()
    
                try:
                    response = brain.think(user_input, history)
                except Exception as e:
                    logger.error(f"Brain error: {e}", exc_info=True)
                    response = f"I encountered an error: {e}"
    
                # Update conversation buffer
                buffer.add("user", user_input)
                buffer.add("assistant", response)
    
                # Display response
                print(f"\n  {settings.assistant_name}: {response}\n")
                logger.info(f"Assistant: {response[:200]}")
    
        except KeyboardInterrupt:
            print(f"\n\n  {settings.assistant_name}: Session terminated. Goodbye, {settings.user_name}.\n")
            logger.info("Session terminated by user (Ctrl+C)")

    logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
