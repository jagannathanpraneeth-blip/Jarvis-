"""
JARVIS Swarm Orchestrator

Coordinates the asynchronous multi-agent system.
"""

import asyncio
from typing import Dict, Any

from core.agent import AutonomousAgent
from core.config import Settings
from core.logger import get_logger

logger = get_logger("swarm")


class Swarm:
    def __init__(self, settings: Settings, brain):
        self.settings = settings
        self.brain = brain
        # Brain holds all the tool declarations from plugins
        self.tools = brain._tools
        self.tool_handlers = brain._tool_handlers
        
    async def spawn_agent(self, name: str, role_prompt: str, goal: str) -> str:
        """Spawns an agent to execute a goal."""
        logger.info(f"Spawning agent: {name} (Goal: {goal})")
        
        agent = AutonomousAgent(
            name=name,
            role_prompt=role_prompt,
            tools=self.tools,
            tool_handlers=self.tool_handlers,
            settings=self.settings
        )
        
        result = await agent.run(goal)
        return result
        
    async def vibe_code(self, goal: str) -> str:
        """Helper to spawn the vibe coding agent."""
        role = (
            "You are an expert autonomous software engineer. "
            "You have full terminal access and can read/write files. "
            "Your goal is to write code, test it, read any errors, and fix them autonomously "
            "until the user's requirements are met perfectly. Be concise in your final report."
        )
        return await self.spawn_agent("CoderAgent", role, goal)
        
    async def browse_web(self, goal: str) -> str:
        """Helper to spawn the browser agent."""
        role = (
            "You are an expert web automation agent. "
            "You have access to a headless browser (Playwright). "
            "You can navigate to URLs, extract text, and click elements. "
            "Achieve the user's web goal autonomously."
        )
        return await self.spawn_agent("BrowserAgent", role, goal)
