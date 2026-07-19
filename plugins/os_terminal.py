"""
OS Terminal Plugin for JARVIS

Provides the LLM with the ability to execute arbitrary terminal commands.
WARNING: This is extremely powerful. Includes safety rails.
"""

import subprocess
import os

from core.logger import get_logger

logger = get_logger("plugin.os_terminal")


def register(brain, settings):
    """Registers the OS Terminal tools with the JARVIS Brain."""
    
    def execute_command(command: str) -> str:
        """Executes a terminal command."""
        
        # --- Safety Rail ---
        if not settings.plugins.god_mode:
            print(f"\n[WARNING] JARVIS is attempting to execute a terminal command:")
            print(f"  Command: {command}")
            try:
                response = input("  Allow execution? [y/N]: ").strip().lower()
                if response != 'y':
                    logger.info("User rejected command execution.")
                    return "ERROR: The user rejected this action. You do not have permission to execute this command."
            except Exception as e:
                return f"ERROR: Failed to get user permission: {e}"
        # -------------------
            
        logger.warning(f"Executing terminal command: {command}")
        
        try:
            # On Windows, we prefer powershell for advanced scripting capabilities
            # Use shell=True to allow shell builtins like 'dir' or 'echo'
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=30, # Prevent hanging commands
                cwd=os.getcwd()
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode == 0:
                if not output:
                    return "Command executed successfully with no output."
                # Truncate to avoid blowing up the context window
                if len(output) > 2000:
                    return output[:2000] + "\n...[OUTPUT TRUNCATED]..."
                return output
            else:
                return f"Command failed with exit code {result.returncode}.\nError: {error}"
                
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds."
        except Exception as e:
            return f"Failed to execute command: {e}"

    # Register the tool
    brain.register_tool(
        name="execute_command",
        description="Executes a command in PowerShell. Use this to run scripts, install packages, check system status, open files/apps (e.g., 'start msedge'), or modify system settings.",
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string", 
                    "description": "The exact PowerShell command to run."
                }
            },
            "required": ["command"]
        },
        handler=execute_command
    )
    
    logger.info("OS Terminal plugin registered.")
