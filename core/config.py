"""
JARVIS Configuration Loader

Loads settings from config/settings.yaml and secrets from .env,
exposing them as a typed Settings dataclass.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Project root — two levels up from core/config.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class BrainSettings:
    model: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    personality_file: str = "config/personality.md"


@dataclass
class MemorySettings:
    buffer_size: int = 20


@dataclass
class LoggingSettings:
    level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "logs"


@dataclass
class VoiceSettings:
    wake_word: str = "hey_jarvis"
    wake_word_threshold: float = 0.5
    stt_model: str = "base.en"
    tts_engine: str = "piper"
    tts_voice: str = "en_US-lessac-medium"
    push_to_talk_key: str = "space"
    silence_threshold: float = 0.02
    silence_duration: float = 1.5
    continuous_conversation: bool = False


@dataclass
class PluginSettings:
    enabled: bool = True
    god_mode: bool = True
    plugin_dir: str = "plugins"


@dataclass
class Settings:
    """Central configuration object for JARVIS."""

    assistant_name: str = "JARVIS"
    user_name: str = "Sir"

    brain: BrainSettings = field(default_factory=BrainSettings)
    memory: MemorySettings = field(default_factory=MemorySettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    plugins: PluginSettings = field(default_factory=PluginSettings)

    # Secrets (loaded from .env, never from YAML)
    gemini_api_key: str = ""

    def validate(self) -> None:
        """Check that required settings are present. Exit with a clear message if not."""
        if not self.gemini_api_key:
            print(
                "\n[JARVIS] ERROR: GEMINI_API_KEY not found.\n"
                "  1. Copy .env.example to .env\n"
                "  2. Paste your Gemini API key\n"
                "  3. Re-run the assistant.\n"
            )
            sys.exit(1)

    @property
    def personality_path(self) -> Path:
        return PROJECT_ROOT / self.brain.personality_file

    @property
    def log_dir_path(self) -> Path:
        return PROJECT_ROOT / self.logging.log_dir


def _build_sub_settings(cls, data: dict[str, Any] | None):
    """Build a dataclass instance from a dict, ignoring unknown keys."""
    if data is None:
        return cls()
    valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in valid_keys}
    return cls(**filtered)


def load_settings() -> Settings:
    """Load configuration from .env and settings.yaml, return a Settings instance."""
    # --- Load .env ---
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=env_path)

    # --- Load YAML ---
    yaml_path = PROJECT_ROOT / "config" / "settings.yaml"
    yaml_data: dict[str, Any] = {}
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}

    # --- Build Settings ---
    settings = Settings(
        assistant_name=yaml_data.get("assistant_name", "JARVIS"),
        user_name=yaml_data.get("user_name", "Sir"),
        brain=_build_sub_settings(BrainSettings, yaml_data.get("brain")),
        memory=_build_sub_settings(MemorySettings, yaml_data.get("memory")),
        logging=_build_sub_settings(LoggingSettings, yaml_data.get("logging")),
        voice=_build_sub_settings(VoiceSettings, yaml_data.get("voice")),
        plugins=_build_sub_settings(PluginSettings, yaml_data.get("plugins")),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
    )

    return settings
