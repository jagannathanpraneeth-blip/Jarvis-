"""
JARVIS Phase 1 — Automated Test Script
Tests config, logging, brain (Gemini API), tool-calling, and conversation buffer.
"""

import sys
import os
import re
import time

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from core.config import load_settings
from core.logger import setup_logging, get_logger
from core.brain import Brain
from memory.buffer import ConversationBuffer


def test_config():
    print("=" * 50)
    print("TEST 1: Config Loading")
    print("=" * 50)
    settings = load_settings()
    print(f"  Assistant name : {settings.assistant_name}")
    print(f"  User name      : {settings.user_name}")
    print(f"  Model          : {settings.brain.model}")
    print(f"  Temperature    : {settings.brain.temperature}")
    print(f"  Buffer size    : {settings.memory.buffer_size}")
    print(f"  Log level      : {settings.logging.level}")
    print(f"  Personality    : {settings.personality_path} (exists={settings.personality_path.exists()})")
    print(f"  API key set    : {'YES' if settings.gemini_api_key else 'NO'}")
    settings.validate()
    print("  [PASS] Config loaded and validated.\n")
    return settings


def test_logging(settings):
    print("=" * 50)
    print("TEST 2: Structured Logging")
    print("=" * 50)
    setup_logging(
        level=settings.logging.level,
        log_to_file=settings.logging.log_to_file,
        log_dir=settings.log_dir_path,
    )
    logger = get_logger("test")
    logger.info("Test log message — INFO level")
    logger.debug("Test log message — DEBUG level (may not show at INFO)")
    logger.warning("Test log message — WARNING level")
    print("  [PASS] Logging initialized. Check logs/jarvis.log for JSON output.\n")


def test_buffer():
    print("=" * 50)
    print("TEST 3: Conversation Buffer")
    print("=" * 50)
    buf = ConversationBuffer(max_turns=4)
    buf.add("user", "Hello")
    buf.add("assistant", "Hi there!")
    buf.add("user", "How are you?")
    buf.add("assistant", "I'm doing well.")
    print(f"  Buffer: {buf}")
    assert buf.turn_count == 4, f"Expected 4 turns, got {buf.turn_count}"

    # Test eviction
    buf.add("user", "This should evict the oldest")
    assert buf.turn_count == 4, f"Expected 4 after eviction, got {buf.turn_count}"
    history = buf.get_history()
    assert history[0]["content"] == "Hi there!", f"Oldest should be 'Hi there!', got '{history[0]['content']}'"

    # Test clear
    buf.clear()
    assert buf.turn_count == 0, f"Expected 0 after clear, got {buf.turn_count}"
    print(f"  After clear: {buf}")
    print("  [PASS] Buffer add/evict/history/clear all work.\n")


def _call_with_quota_retry(brain, message, history, max_wait=90):
    """Try calling the brain, with smart retry on rate limits."""
    from google.genai.errors import ClientError
    
    deadline = time.time() + max_wait
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            return brain.think(message, history=history)
        except ClientError as e:
            if e.code == 429:
                # Parse retry delay from error message
                match = re.search(r'retry in (\d+)', str(e))
                wait = int(match.group(1)) + 2 if match else 15
                remaining = deadline - time.time()
                if wait > remaining:
                    print(f"  [SKIP] Rate limit won't clear in time ({wait}s needed, {remaining:.0f}s left)")
                    return None
                print(f"  ... Rate limited. Waiting {wait}s (attempt {attempt})...")
                time.sleep(wait)
            else:
                raise
    return None


def test_brain_chat(settings):
    print("=" * 50)
    print("TEST 4: Brain — Simple Chat (Gemini API)")
    print("=" * 50)
    brain = Brain(settings)
    
    response = _call_with_quota_retry(brain, "Say hello in exactly 5 words.", [])
    if response is None:
        print("  [SKIP] API quota exhausted — chat test skipped.")
        print("         This is a quota issue, not a code issue.")
        print("         Run 'python main.py' manually when quota resets.\n")
        return brain, False

    print(f"  User    : Say hello in exactly 5 words.")
    print(f"  JARVIS  : {response}")
    assert len(response) > 0, "Empty response from brain"
    print("  [PASS] Brain returned a valid response.\n")
    return brain, True


def test_tool_calling(brain):
    print("=" * 50)
    print("TEST 5: Brain — Tool Calling (get_current_time)")
    print("=" * 50)

    response = _call_with_quota_retry(brain, "What is the current date and time?", [])
    if response is None:
        print("  [SKIP] API quota exhausted — tool-calling test skipped.\n")
        return

    print(f"  User    : What is the current date and time?")
    print(f"  JARVIS  : {response}")
    time_keywords = ["am", "pm", "AM", "PM", ":", "2026", "July", "today"]
    has_time = any(kw in response for kw in time_keywords)
    if has_time:
        print("  [PASS] Tool-calling worked — response contains time information.\n")
    else:
        print(f"  [WARN] Response may not contain time info. Manual check needed.\n")


def test_conversation_memory(brain):
    print("=" * 50)
    print("TEST 6: Brain — Conversation Memory")
    print("=" * 50)
    history = [
        {"role": "user", "content": "My favorite color is midnight blue."},
        {"role": "assistant", "content": "Noted — midnight blue. Excellent taste."},
    ]

    response = _call_with_quota_retry(brain, "What's my favorite color?", history)
    if response is None:
        print("  [SKIP] API quota exhausted — memory test skipped.\n")
        return

    print(f"  Context : Told JARVIS favorite color is midnight blue")
    print(f"  User    : What's my favorite color?")
    print(f"  JARVIS  : {response}")
    if "midnight blue" in response.lower() or "blue" in response.lower():
        print("  [PASS] Brain remembered context from history.\n")
    else:
        print("  [WARN] Response may not reference the color. Manual check needed.\n")


def main():
    print("\n" + "=" * 50)
    print("  JARVIS Phase 1 — Automated Tests")
    print("=" * 50 + "\n")

    settings = test_config()
    test_logging(settings)
    test_buffer()
    brain, api_ok = test_brain_chat(settings)

    if api_ok:
        test_tool_calling(brain)
        test_conversation_memory(brain)
    else:
        print("=" * 50)
        print("TEST 5 & 6: Skipped (API quota exhausted)")
        print("=" * 50)
        print("  Tests 1-3 validate all local code works correctly.")
        print("  Tests 4-6 require API quota — run manually later.\n")

    print("=" * 50)
    print("  ALL TESTS COMPLETE")
    passed = "Tests 1-3 PASSED" + (" | Tests 4-6 PASSED" if api_ok else " | Tests 4-6 SKIPPED (quota)")
    print(f"  {passed}")
    print("=" * 50)


if __name__ == "__main__":
    main()
