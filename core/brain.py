"""
JARVIS Brain — LLM Interface

Connects to NVIDIA NIM via the OpenAI SDK.
Handles conversation history, system prompts, and tool-calling.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Callable
from core.state import set_state, emit_event

from openai import OpenAI, AsyncOpenAI

from core.config import Settings
from core.logger import get_logger
from core.plugin_manager import PluginManager

logger = get_logger("brain")


# ── Built-in demo tool ──────────────────

def _get_current_time(**kwargs) -> str:
    """Returns the current date and time."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M:%S %p")


BUILTIN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the current local date and time.",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    }
]

BUILTIN_TOOL_HANDLERS: dict[str, Callable[..., str]] = {
    "get_current_time": _get_current_time,
}


class Brain:
    """
    The LLM reasoning engine for JARVIS.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        
        # Initialize OpenAI clients pointing to NVIDIA
        base_url = "https://integrate.api.nvidia.com/v1"
        self._client = OpenAI(base_url=base_url, api_key=settings.nvidia_api_key)
        self.async_client = AsyncOpenAI(base_url=base_url, api_key=settings.nvidia_api_key)
        
        self._model = settings.brain.model

        self._system_prompt = self._load_personality()

        self._tool_handlers: dict[str, Callable[..., str]] = dict(BUILTIN_TOOL_HANDLERS)
        self._tools: list[dict] = list(BUILTIN_TOOLS)

        # Load dynamic plugins
        self._plugin_manager = PluginManager(settings, self)
        self._plugin_manager.load_all()

        logger.info(
            f"Brain initialized — model={self._model}, "
            f"tools={list(self._tool_handlers.keys())}"
        )

    def _load_personality(self) -> str:
        """Load the system prompt from personality.md."""
        path = self._settings.personality_path
        try:
            text = path.read_text(encoding="utf-8")
            text = text.replace("{user_name}", self._settings.user_name)
            logger.info(f"Personality loaded from {path}")
            return text
        except FileNotFoundError:
            logger.warning(f"Personality file not found at {path}, using default")
            return f"You are {self._settings.assistant_name}, a helpful personal assistant."

    def think(self, user_message: str, history: list[dict[str, str]]) -> str:
        """
        Send a message to the LLM with conversation history and tools.
        (Synchronous version for the simple text chat).
        """
        set_state("thinking")
        # Build OpenAI message format
        messages = [{"role": "system", "content": self._system_prompt}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_message})

        max_iterations = 10
        for iteration in range(max_iterations):
            start = time.time()
            logger.debug(f"Calling NVIDIA API (iteration {iteration + 1})")

            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=self._settings.brain.temperature,
                    max_tokens=self._settings.brain.max_output_tokens,
                    tools=self._tools if self._tools else None,
                    tool_choice="auto" if self._tools else "none",
                    # Add extra args for models like nemotron
                    extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":self._settings.brain.max_output_tokens}
                )
            except Exception as e:
                logger.error(f"API Error: {e}", exc_info=True)
                return f"I encountered an API error: {e}"

            message = response.choices[0].message
            
            # Print reasoning if available (for UI/CLI)
            reasoning = None
            if hasattr(message, "model_extra") and message.model_extra and "reasoning_content" in message.model_extra:
                reasoning = message.model_extra['reasoning_content']
            elif hasattr(message, "reasoning_content") and getattr(message, "reasoning_content"):
                reasoning = getattr(message, 'reasoning_content')
                
            if reasoning:
                print(f"\n[Thinking]\n{reasoning}\n")
                emit_event('thought', {'text': reasoning})

            if not message.tool_calls:
                set_state("idle")
                return message.content or "I processed your request but have nothing to add."

            # Add assistant's tool call request to messages
            messages.append(message)

            # Execute tools
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except Exception:
                    tool_args = {}

                logger.info(f"Tool call: {tool_name}({tool_args})")
                emit_event('tool_call', {'name': tool_name, 'args': tool_args})

                handler = self._tool_handlers.get(tool_name)
                if handler:
                    try:
                        result = handler(**tool_args)
                        logger.info(f"Tool result: {tool_name} -> {str(result)[:100]}")
                        emit_event('tool_result', {'name': tool_name, 'result': str(result)[:200]})
                    except Exception as e:
                        result = f"Error executing {tool_name}: {e}"
                        logger.error(result)
                        emit_event('tool_error', {'name': tool_name, 'error': str(e)})
                else:
                    result = f"Tool '{tool_name}' is not available."
                    logger.warning(result)
                    emit_event('tool_error', {'name': tool_name, 'error': result})

                # Add tool response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)[:5000] # Truncate to prevent context window explosion
                })

        set_state("idle")
        return "I got stuck in a loop trying to use my tools."

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., str],
    ) -> None:
        """
        Register a tool using OpenAI JSON Schema format.
        """
        self._tool_handlers[name] = handler

        tool_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
        
        self._tools.append(tool_def)
        logger.info(f"Registered tool: {name}")
