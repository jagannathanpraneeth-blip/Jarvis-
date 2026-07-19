"""
JARVIS Autonomous Agent

Represents a single sub-agent in the Swarm capable of looping
autonomously to achieve a specific goal.
"""
import asyncio
from typing import Any, Callable

from google import genai
from google.genai import types

from core.logger import get_logger

logger = get_logger("agent")

class AutonomousAgent:
    def __init__(self, name: str, role_prompt: str, tools: list[types.Tool], tool_handlers: dict, settings):
        self.name = name
        self.role_prompt = role_prompt
        self.tools = tools
        self.tool_handlers = tool_handlers
        
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.brain.model
        
    async def run(self, goal: str, max_iterations: int = 15) -> str:
        """Runs the autonomous loop to achieve the goal."""
        logger.info(f"Agent '{self.name}' starting goal: {goal}")
        
        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text=goal)])
        ]
        
        gen_config = types.GenerateContentConfig(
            system_instruction=self.role_prompt,
            tools=self.tools if self.tools else None,
            temperature=0.2, # Lower temp for more deterministic agent behavior
        )
        
        for i in range(max_iterations):
            logger.debug(f"Agent '{self.name}' loop {i+1}/{max_iterations}")
            
            try:
                # Use the async client
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=gen_config
                )
            except Exception as e:
                logger.error(f"Agent '{self.name}' API error: {e}")
                return f"Agent '{self.name}' failed due to API error: {e}"
                
            candidate = response.candidates[0] if response.candidates else None
            if not candidate:
                return f"Agent '{self.name}' received no response."
                
            contents.append(candidate.content)
            
            parts = candidate.content.parts if candidate.content else []
            function_calls = [p for p in parts if p.function_call]
            
            if not function_calls:
                # Agent decided it's done or wants to talk
                final_text = " ".join(p.text for p in parts if p.text).strip()
                logger.info(f"Agent '{self.name}' finished: {final_text[:100]}...")
                return final_text
                
            # Execute tools
            function_response_parts = []
            for part in function_calls:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}
                
                logger.info(f"[{self.name}] calling {tool_name}")
                handler = self.tool_handlers.get(tool_name)
                
                if handler:
                    try:
                        # Handle async and sync tools seamlessly
                        if asyncio.iscoroutinefunction(handler):
                            result = await handler(**tool_args)
                        else:
                            result = handler(**tool_args)
                    except Exception as e:
                        result = f"Error: {e}"
                else:
                    result = f"Tool {tool_name} not found."
                    
                function_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": str(result)[:5000]} # Limit result length
                    )
                )
                
            contents.append(types.Content(role="user", parts=function_response_parts))
            
        logger.warning(f"Agent '{self.name}' hit max iterations.")
        return f"Agent '{self.name}' timed out after {max_iterations} steps."
