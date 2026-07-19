"""
JARVIS Structured Logging

Console output: human-readable, colored.
File output: JSON lines for structured analysis.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON for file output."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Attach any extra fields passed via `extra={...}`
        for key in ("tool", "action", "result", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console output with level coloring."""

    COLORS = {
        "DEBUG": "\033[90m",     # grey
        "INFO": "\033[36m",      # cyan
        "WARNING": "\033[33m",   # yellow
        "ERROR": "\033[31m",     # red
        "CRITICAL": "\033[91m",  # bright red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")
        return (
            f"{color}[{timestamp}] {record.levelname:<8}{self.RESET} "
            f"{record.name}: {record.getMessage()}"
        )


def setup_logging(level: str = "INFO", log_to_file: bool = True, log_dir: str | Path = "logs") -> None:
    """Configure root logger with console and optional file handlers."""
    root = logging.getLogger()

    # Avoid duplicate handlers on repeated calls
    if root.handlers:
        return

    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # --- Console handler ---
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ConsoleFormatter())
    root.addHandler(console)

    # --- File handler (JSON lines) ---
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_path / "jarvis.log", encoding="utf-8"
        )
        file_handler.setFormatter(JsonFormatter())
        root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. All JARVIS modules should use this."""
    return logging.getLogger(f"jarvis.{name}")
