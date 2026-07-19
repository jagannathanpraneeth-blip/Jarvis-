"""
JARVIS Brain — LLM Interface

Connects to Google Gemini via the official google-genai SDK.
Handles conversation history, system prompts, and tool-calling.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Callable

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from core.config import Settings
from core.logger import get_logger
from core.plugin_manager import PluginManager

logger = get_logger("brain")


# ── Built-in demo tool (verifies tool-calling works) ──────────────────

def _get_current_time(**kwargs) -> str:
    """Returns the current date and time."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M:%S %p")


# Tool schema for Gemini function-calling
BUILTIN_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_current_time",
                description="Returns the current local date and time. Use this when the user asks what time or date it is.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={},
                ),
            )
        ]
    )
]

# Map of tool name -> callable
BUILTIN_TOOL_HANDLERS: dict[str, Callable[..., str]] = {
    "get_current_time": _get_current_time,
}


class Brain:
    """
    The LLM reasoning engine for JARVIS.

    Manages the Gemini client, conversation history, system prompt,
    and the tool-calling loop.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.brain.model

        # Load personality / system prompt
        self._system_prompt = self._load_personality()

        # Tool registry: name -> handler function
        self._tool_handlers: dict[str, Callable[..., str]] = dict(BUILTIN_TOOL_HANDLERS)

        # Tool declarations for the API
        self._tools: list[types.Tool] = list(BUILTIN_TOOLS)

        # Load dynamic plugins
        self._plugin_manager = PluginManager(settings, self)
        self._plugin_manager.load_all()

        logger.info(
            f"Brain initialized — model={self._model}, "
            f"tools={list(self._tool_handlers.keys())}"
        )

    def _load_personality(self) -> str:
        """Load the system prompt from personality.md, with variable substitution."""
        path = self._settings.personality_path
        try:
            text = path.read_text(encoding="utf-8")
            # Replace template variables
            text = text.replace("{user_name}", self._settings.user_name)
            logger.info(f"Personality loaded from {path}")
            return text
        except FileNotFoundError:
            logger.warning(f"Personality file not found at {path}, using default")
            return f"You are {self._settings.assistant_name}, a helpful personal assistant."

    def think(self, user_message: str, history: list[dict[str, str]]) -> str:
        """
        Send a message to the LLM with conversation history and tools.
        Handles the tool-calling loop: if the model returns a function call,
        execute it and feed the result back until we get a text response.

        Args:
            user_message: The latest user input.
            history: Previous turns as [{"role": "user"|"assistant", "content": "..."}].

        Returns:
            The assistant's final text response.
        """
        # Build the contents list from history + current message
        contents = []
        for turn in history:
            role = "user" if turn["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        # Generation config
        gen_config = types.GenerateContentConfig(
            system_instruction=self._system_prompt,
            temperature=self._settings.brain.temperature,
            max_output_tokens=self._settings.brain.max_output_tokens,
            tools=self._tools if self._tools else None,
        )

        # Tool-calling loop — iterate until we get a text response
        max_iterations = 10  # safety limit
        for iteration in range(max_iterations):
            start = time.time()

            logger.debug(f"Calling Gemini (iteration {iteration + 1})")

            # Retry with backoff on rate-limit errors
            max_retries = 3
            for retry in range(max_retries + 1):
                try:
                    response = self._client.models.generate_content(
                        model=self._model,
                        contents=contents,
                        config=gen_config,
                    )
                    break
                except ClientError as e:
                    if e.code == 429 and retry < max_retries:
                        wait = 5 * (2 ** retry)  # 5s, 10s, 20s
                        logger.warning(f"Rate limited (429). Retrying in {wait}s... ({retry + 1}/{max_retries})")
                        time.sleep(wait)
                    else:
                        raise

            duration_ms = int((time.time() - start) * 1000)
            logger.info(f"Gemini responded in {duration_ms}ms", extra={"duration_ms": duration_ms})

            # Check if the response contains a function call
            candidate = response.candidates[0] if response.candidates else None
            if candidate is None:
                logger.error("No candidates in Gemini response")
                return "I'm sorry, I didn't get a response. Could you try again?"

            parts = candidate.content.parts if candidate.content else []

            # Look for function calls in the response parts
            function_calls = [p for p in parts if p.function_call]
            text_parts = [p for p in parts if p.text]

            if not function_calls:
                # No tool calls — extract and return text
                final_text = " ".join(p.text for p in text_parts if p.text).strip()
                if final_text:
                    return final_text
                return "I processed your request but have nothing to add."

            # Execute each function call and build function responses
            # First, add the model's response (with function calls) to contents
            contents.append(candidate.content)

            function_response_parts = []
            for part in function_calls:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                logger.info(
                    f"Tool call: {tool_name}({tool_args})",
                    extra={"tool": tool_name, "action": "call"},
                )

                # Execute the tool
                handler = self._tool_handlers.get(tool_name)
                if handler:
                    try:
                        result = handler(**tool_args)
                        logger.info(
                            f"Tool result: {tool_name} -> {result[:100]}",
                            extra={"tool": tool_name, "action": "result", "result": result},
                        )
                    except Exception as e:
                        result = f"Error executing {tool_name}: {e}"
                        logger.error(result, extra={"tool": tool_name, "action": "error"})
                else:
                    result = f"Tool '{tool_name}' is not available."
                    logger.warning(result, extra={"tool": tool_name, "action": "not_found"})

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result},
                    )
                )

            # Add function responses to contents and loop back
            contents.append(types.Content(role="user", parts=function_response_parts))

        logger.error("Tool-calling loop exceeded max iterations")
        return "I got stuck in a loop trying to use my tools. Could you rephrase your request?"

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., str],
    ) -> None:
        """
        Register an external tool (for plugin system in Phase 4).

        Args:
            name: Unique tool name.
            description: What the tool does (shown to the LLM).
            parameters: JSON Schema for the tool's parameters.
            handler: Callable that executes the tool.
        """
        self._tool_handlers[name] = handler

        # Build schema properties
        props = {}
        required = []
        for prop_name, prop_info in parameters.get("properties", {}).items():
            prop_type = prop_info.get("type", "string").upper()
            schema_type = getattr(types.Type, prop_type, types.Type.STRING)
            props[prop_name] = types.Schema(
                type=schema_type,
                description=prop_info.get("description", ""),
            )
            if prop_name in parameters.get("required", []):
                required.append(prop_name)

        new_func_decl = types.FunctionDeclaration(
            name=name,
            description=description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties=props,
                required=required if required else None,
            )
        )
        
        # If we already have a tool, add to its function declarations, else create new tool
        if self._tools:
            # We assume we just append to the first Tool object's function_declarations
            # as Gemini allows multiple function declarations in one Tool.
            if not self._tools[0].function_declarations:
                self._tools[0].function_declarations = []
            self._tools[0].function_declarations.append(new_func_decl)
        else:
            self._tools.append(types.Tool(function_declarations=[new_func_decl]))
            
        logger.debug(f"Registered tool: {name}")
        logger.info(f"Registered tool: {name}")
