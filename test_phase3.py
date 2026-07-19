"""
Test Phase 3 Plugins (Offline)
Verifies PluginManager, OS Terminal, and Workspace tools.
"""

from core.config import load_settings
from core.plugin_manager import PluginManager

class DummyBrain:
    def __init__(self):
        self.tools = {}
        
    def register_tool(self, name, description, parameters, handler):
        self.tools[name] = handler
        print(f"  [+] Registered Tool: {name}")

def run_tests():
    print("\n=== JARVIS Phase 3 Offline Tests ===\n")
    
    # 1. Test Config & Plugin Loader
    print("TEST 1: Plugin Manager")
    settings = load_settings()
    # Force god mode for the test
    settings.plugins.god_mode = True 
    
    brain = DummyBrain()
    manager = PluginManager(settings, brain)
    manager.load_all()
    
    if not brain.tools:
        print("  [FAIL] No tools registered.")
        return
    print("  [PASS] Plugins loaded successfully.\n")
    
    # 2. Test Workspace Plugin
    print("TEST 2: Workspace Plugin")
    write_file = brain.tools.get("write_file")
    read_file = brain.tools.get("read_file")
    list_dir = brain.tools.get("list_directory")
    
    if write_file and read_file and list_dir:
        test_file = "test_workspace_plugin.txt"
        test_content = "Hello from Phase 3!"
        
        write_res = write_file(test_file, test_content)
        print(f"  Write: {write_res}")
        
        read_res = read_file(test_file)
        print(f"  Read: {read_res}")
        
        if read_res == test_content:
            print("  [PASS] Read/Write successful.")
        else:
            print("  [FAIL] Content mismatch.")
            
        import os
        if os.path.exists(test_file):
            os.remove(test_file)
    else:
        print("  [FAIL] Workspace tools not found.\n")
        
    print("\nTEST 3: OS Terminal Plugin")
    execute = brain.tools.get("execute_command")
    if execute:
        # Run a safe command like "echo Hello"
        res = execute("echo Hello from Terminal")
        print(f"  Terminal Output: {res}")
        if "Hello from Terminal" in res:
            print("  [PASS] OS Terminal executed successfully.")
        else:
            print("  [FAIL] Unexpected output.")
    else:
        print("  [FAIL] execute_command tool not found.")

if __name__ == "__main__":
    run_tests()
