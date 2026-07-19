"""
Test Phase 6 (Safety Rails & Ambient Context)
"""

import os
from core.config import load_settings
from core.plugin_manager import PluginManager

class DummyBrain:
    def __init__(self):
        self.tools = {}
        
    def register_tool(self, name, description, parameters, handler):
        self.tools[name] = handler
        print(f"  [+] Registered Tool: {name}")

def run_tests():
    print("\n=== JARVIS Phase 6 Test ===\n")
    
    settings = load_settings()
    
    # 1. Test Ambient Context Plugins
    print("TEST 1: Ambient Context Plugins")
    brain = DummyBrain()
    manager = PluginManager(settings, brain)
    manager.load_all()
    
    print("\n--- Testing Clipboard ---")
    read_clipboard = brain.tools.get("read_clipboard")
    if read_clipboard:
        try:
            res = read_clipboard()
            print(f"  Clipboard Output: {res[:50]}...")
        except Exception as e:
            print(f"  [WARN] Clipboard failed (expected in headless): {e}")
            
    print("\n--- Testing Active Window ---")
    get_window = brain.tools.get("get_active_window")
    if get_window:
        try:
            res = get_window()
            print(f"  Window Output: {res}")
        except Exception as e:
            print(f"  [WARN] Window failed (expected in headless): {e}")
            
    print("\n--- Testing Screenshot (Hybrid Vision) ---")
    # For testing, we won't actually trigger it if the key isn't set
    # because pyautogui.screenshot() will crash on headless without xvfb
    # But we can verify it was registered!
    if "take_screenshot" in brain.tools:
        print("  [PASS] take_screenshot tool registered and ready for Hybrid Vision.")

    print("\n--------------------------------------------------")
    print("TEST 2: Safety Rails (God Mode = False)")
    print("--------------------------------------------------")
    
    # Turn off god mode
    settings.plugins.god_mode = False
    
    execute = brain.tools.get("execute_command")
    if execute:
        print("  Attempting to run command with god_mode=False...")
        # Since we can't easily pipe 'n' in the same Python process without mocking input,
        # we will monkey-patch builtins.input just for the test
        import builtins
        original_input = builtins.input
        def mock_input(prompt):
            print(prompt, end="")
            print("n (Mocked User Input)")
            return "n"
        
        builtins.input = mock_input
        
        try:
            res = execute("echo DANGER")
            print(f"\n  Result: {res}")
            if "rejected" in res:
                print("\n  [PASS] Safety rail correctly blocked execution and returned rejection to LLM.")
            else:
                print("\n  [FAIL] Safety rail failed to block execution.")
        finally:
            builtins.input = original_input

if __name__ == "__main__":
    run_tests()
