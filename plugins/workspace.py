"""
Workspace Plugin for JARVIS

Provides tools for reading, writing, and listing files.
Crucial for autonomous coding.
"""

import os
from pathlib import Path

from core.logger import get_logger

logger = get_logger("plugin.workspace")


def register(brain, settings):
    """Registers the Workspace tools with the JARVIS Brain."""
    
    def read_file(filepath: str) -> str:
        """Reads the content of a file."""
        try:
            path = Path(filepath).resolve()
            if not path.exists():
                return f"Error: File '{filepath}' does not exist."
            if not path.is_file():
                return f"Error: '{filepath}' is a directory, not a file."
                
            content = path.read_text(encoding="utf-8")
            if len(content) > 5000:
                return content[:5000] + "\n\n...[FILE TRUNCATED DUE TO LENGTH]..."
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    def write_file(filepath: str, content: str) -> str:
        """Writes content to a file (overwrites)."""
        try:
            path = Path(filepath).resolve()
            # Ensure parent directories exist
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} characters to '{filepath}'."
        except Exception as e:
            return f"Error writing file: {e}"
            
    def list_directory(dir_path: str = ".") -> str:
        """Lists files and folders in a directory."""
        try:
            path = Path(dir_path).resolve()
            if not path.exists():
                return f"Error: Directory '{dir_path}' does not exist."
                
            items = []
            for item in path.iterdir():
                type_str = "DIR " if item.is_dir() else "FILE"
                items.append(f"[{type_str}] {item.name}")
                
            if not items:
                return f"Directory '{dir_path}' is empty."
            return "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {e}"

    # Register tools
    brain.register_tool(
        name="read_file",
        description="Reads the contents of a local file. Use this to inspect code, configuration, or text.",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Absolute or relative path to the file."}
            },
            "required": ["filepath"]
        },
        handler=read_file
    )
    
    brain.register_tool(
        name="write_file",
        description="Writes complete content to a local file. Overwrites the file if it exists.",
        parameters={
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path to the file to create or overwrite."},
                "content": {"type": "string", "description": "The exact content to write into the file."}
            },
            "required": ["filepath", "content"]
        },
        handler=write_file
    )
    
    brain.register_tool(
        name="list_directory",
        description="Lists all files and subdirectories in a given folder.",
        parameters={
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "Path to the directory to list. Defaults to '.' (current dir)."}
            },
            "required": []
        },
        handler=list_directory
    )
    
    logger.info("Workspace plugin registered.")
