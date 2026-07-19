"""
JARVIS Conversation Buffer

Rolling short-term memory: keeps the last N conversation turns
and feeds them to the LLM as context each call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from core.logger import get_logger

logger = get_logger("memory.buffer")


@dataclass
class Turn:
    """A single conversation turn."""
    role: Literal["user", "assistant"]
    content: str


class ConversationBuffer:
    """Fixed-size rolling buffer of conversation turns."""

    def __init__(self, max_turns: int = 20) -> None:
        self._max_turns = max_turns
        self._turns: list[Turn] = []
        logger.info(f"Conversation buffer initialized (max {max_turns} turns)")

    def add(self, role: Literal["user", "assistant"], content: str) -> None:
        """Add a turn to the buffer, evicting the oldest if full."""
        self._turns.append(Turn(role=role, content=content))
        if len(self._turns) > self._max_turns:
            evicted = self._turns.pop(0)
            logger.debug(f"Evicted oldest turn: {evicted.role}: {evicted.content[:50]}...")

    def get_history(self) -> list[dict[str, str]]:
        """Return the buffer as a list of dicts for the LLM API."""
        return [{"role": t.role, "content": t.content} for t in self._turns]

    def clear(self) -> None:
        """Wipe the buffer."""
        self._turns.clear()
        logger.info("Conversation buffer cleared")

    @property
    def turn_count(self) -> int:
        return len(self._turns)

    def __repr__(self) -> str:
        return f"ConversationBuffer({self.turn_count}/{self._max_turns} turns)"
