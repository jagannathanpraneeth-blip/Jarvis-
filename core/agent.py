"""
JARVIS Autonomous Agent

Represents a single sub-agent in the Swarm capable of looping
autonomously to achieve a specific goal using the OpenAI SDK (NVIDIA NIM).
"""
import asyncio
import json
from typing import List, Dict, Any, Callable
import os

from openai import AsyncOpenAI
from core.logger import get_logger
from core.state import set_state

logger = get_logger("agent")

class AutonomousAgent:
    def __init__(self, name: str, role_prompt: str, tools: list[dict], tool_handlers: dict, settings):
        self.name = name
        self.role_prompt = role_prompt
        self.tools = tools
        self.tool_handlers = tool_handlers
        self._settings = settings
        
        self.client = AsyncOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=settings.nvidia_api_key
        )
        self.model = settings.brain.model
        self.total_tool_calls = 0
        
    async def run(self, goal: str, max_iterations: int = 15) -> str:
        """Runs the autonomous loop to achieve the goal."""
        logger.info(f"Agent '{self.name}' starting goal: {goal}")
        
        set_state("thinking", f"Agent {self.name} is running")
        try:
            # Build initial messages
            messages = [{"role": "system", "content": self.role_prompt}]
            messages.append({"role": "user", "content": f"Your Goal:\n{goal}"})
            
            for iteration in range(max_iterations):
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.2,
                        max_tokens=2048,
                        tools=self.tools,
                        tool_choice="auto",
                        extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":2048}
                    )
                except Exception as e:
                    logger.error(f"Agent '{self.name}' API error: {e}")
                    return f"Agent '{self.name}' failed due to API error: {e}"
                    
                message = response.choices[0].message
                
                # Print thinking if available
                if hasattr(message, "model_extra") and message.model_extra and "reasoning_content" in message.model_extra:
                    print(f"\n[{self.name} Thinking]\n{message.model_extra['reasoning_content']}\n")
                elif hasattr(message, "reasoning_content") and getattr(message, "reasoning_content"):
                    print(f"\n[{self.name} Thinking]\n{getattr(message, 'reasoning_content')}\n")
    
                if not message.tool_calls:
                    final_result = message.content or "Completed without output."
                    logger.info(f"Agent '{self.name}' finished: {final_result[:100]}...")
                    return final_result
                    
                messages.append(message)
                
                # Execute tools
                for tool_call in message.tool_calls:
                    
                    # --- Rate Limiter Safety Rail ---
                    self.total_tool_calls += 1
                    if self.total_tool_calls > 15:
                        logger.error(f"Agent '{self.name}' exceeded maximum tool calls (15).")
                        return f"ERROR: Runaway loop detected. Terminating agent after 15 tool calls."
                    # --------------------------------
                    
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except Exception:
                        tool_args = {}
                        
                    logger.info(f"[{self.name}] calling {tool_name}")
                    
                    handler = self.tool_handlers.get(tool_name)
                    if handler:
                        try:
                            # Safely handle async tools if any exist
                            if asyncio.iscoroutinefunction(handler):
                                result = await handler(**tool_args)
                            else:
                                result = handler(**tool_args)
                        except Exception as e:
                            result = f"Error: {e}"
                    else:
                        result = f"Unknown tool: {tool_name}"
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)[:2000]
                    })
                    
            return f"Agent '{self.name}' failed to achieve goal within {max_iterations} iterations."
        finally:
            set_state("idle", "")
