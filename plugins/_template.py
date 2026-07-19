"""
JARVIS Plugin Template
======================

Copy this file to create a new plugin. Each plugin is a single Python file
in the /plugins directory that gets auto-discovered at startup (Phase 4).

A plugin must define:
  1. PLUGIN_NAME   — unique identifier string
  2. PLUGIN_DESC   — human-readable description for the LLM
  3. TOOLS         — list of tool schema dicts (name, description, parameters)
  4. execute()     — function that receives a tool name + args and returns a result

See the example below.
"""

# --- Plugin Metadata ---
PLUGIN_NAME = "example"
PLUGIN_DESC = "An example plugin that echoes input back."

# --- Tool Schemas (OpenAPI-style, for LLM function-calling) ---
TOOLS = [
    {
        "name": "echo",
        "description": "Echoes the input text back to the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to echo back.",
                }
            },
            "required": ["text"],
        },
    }
]


# --- Execution ---
def execute(tool_name: str, args: dict) -> str:
    """
    Called when the LLM invokes one of this plugin's tools.

    Args:
        tool_name: Which tool was called (matches a name in TOOLS).
        args: The arguments the LLM provided, parsed as a dict.

    Returns:
        A string result to feed back to the LLM.
    """
    if tool_name == "echo":
        return f"Echo: {args.get('text', '')}"
    return f"Unknown tool: {tool_name}"
