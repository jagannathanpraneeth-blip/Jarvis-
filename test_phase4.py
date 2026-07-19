"""
Test Phase 4 (The Swarm)
Tests the Asynchronous Agent Framework and Playwright plugin using the live API.
"""

import asyncio
import os

from core.config import load_settings
from core.plugin_manager import PluginManager
from core.brain import Brain
from core.swarm import Swarm
from core.logger import setup_logging

async def run_tests():
    print("\n=== JARVIS Phase 4 Live Swarm Test ===\n")
    
    settings = load_settings()
    settings.plugins.god_mode = True # Ensure permissions
    setup_logging(level="INFO")
    
    print("[*] Initializing Brain and loading plugins...")
    # The brain will automatically initialize the PluginManager and load tools
    brain = Brain(settings)
    
    print("[*] Initializing Swarm...")
    swarm = Swarm(settings, brain)
    
    print("\n--------------------------------------------------")
    print("TEST 1: Autonomous Web Agent (Playwright)")
    print("--------------------------------------------------")
    print("Goal: Go to example.com and tell me what the main heading is.")
    
    try:
        result = await swarm.browse_web("Navigate to https://example.com and tell me the exact text of the <h1> heading on the page.")
        print(f"\n[AGENT RESULT]:\n{result}")
        if "Example Domain" in result:
             print("\n  [PASS] Browser Agent successfully navigated and extracted text.")
        else:
             print("\n  [WARN] Agent completed but output was unexpected.")
    except Exception as e:
        print(f"\n  [FAIL] Web Agent Test failed: {e}")

    print("\n--------------------------------------------------")
    print("TEST 2: Autonomous Coder Agent (OS Terminal & Workspace)")
    print("--------------------------------------------------")
    print("Goal: Write a python script that calculates 5 factorial, run it, and tell me the output.")
    
    try:
        result = await swarm.vibe_code("Write a python script called 'test_math.py' that prints the factorial of 5. Run the script using the OS Terminal plugin, read the output, and tell me the result.")
        print(f"\n[AGENT RESULT]:\n{result}")
        if "120" in result:
             print("\n  [PASS] Coder Agent successfully wrote, executed, and read the script.")
        else:
             print("\n  [WARN] Agent completed but output was unexpected.")
             
        # Cleanup
        if os.path.exists("test_math.py"):
            os.remove("test_math.py")
    except Exception as e:
        print(f"\n  [FAIL] Coder Agent Test failed: {e}")

if __name__ == "__main__":
    # Playwright requires the proactor event loop on Windows
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_tests())
