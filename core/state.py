"""
JARVIS Global State Manager

Used for inter-process communication (IPC) between the main AI brain
and the HUD Overlay process.
"""

import json
import os
import time
from pathlib import Path

STATE_FILE = Path("temp/state.json")


def _ensure_dir():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def set_state(status: str, message: str = ""):
    """
    Sets the current JARVIS state.
    Statuses: 'idle', 'listening', 'thinking', 'speaking'
    """
    _ensure_dir()
    data = {
        "status": status,
        "message": message,
        "timestamp": time.time()
    }
    
    # Write to a tmp file and rename for atomicity
    tmp_file = STATE_FILE.with_suffix(".tmp")
    try:
        tmp_file.write_text(json.dumps(data), encoding="utf-8")
        tmp_file.replace(STATE_FILE)
    except Exception:
        pass


def get_state() -> dict:
    """Reads the current state."""
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"status": "idle", "message": "", "timestamp": 0}

# ── In-Memory Event Bus for Telemetry ──
_subscribers = []

def subscribe_events(callback):
    """Register a callback for telemetry events."""
    _subscribers.append(callback)

def emit_event(event_type: str, data: dict = None):
    """
    Emit an event to all subscribers.
    Examples: 
      emit_event('tool_call', {'name': 'browser_navigate', 'args': '{...}'})
      emit_event('thought', {'text': 'I need to search for X...'})
    """
    if data is None:
        data = {}
    
    event = {"type": event_type, **data, "timestamp": time.time()}
    for callback in _subscribers:
        try:
            callback(event)
        except Exception:
            pass
