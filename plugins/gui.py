import pyautogui
from core.logger import get_logger

logger = get_logger("plugin.gui")

# Safety configuration for PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5


def _mouse_move(x: int, y: int) -> str:
    try:
        pyautogui.moveTo(x, y, duration=0.3)
        return f"Mouse successfully moved to ({x}, {y})"
    except Exception as e:
        return f"Failed to move mouse: {e}"
        
def _mouse_click(x: int = None, y: int = None, button: str = "left", clicks: int = 1) -> str:
    try:
        kwargs = {"button": button, "clicks": clicks}
        if x is not None and y is not None:
            kwargs["x"] = x
            kwargs["y"] = y
            
        pyautogui.click(**kwargs)
        pos_str = f"at ({x}, {y})" if x is not None else "at current location"
        return f"Successfully executed {clicks} {button} click(s) {pos_str}."
    except Exception as e:
        return f"Failed to click mouse: {e}"
        
def _keyboard_type(text: str, interval: float = 0.05) -> str:
    try:
        pyautogui.write(text, interval=interval)
        return f"Successfully typed text: '{text}'"
    except Exception as e:
        return f"Failed to type text: {e}"
        
def _keyboard_press(keys: list[str]) -> str:
    try:
        pyautogui.hotkey(*keys)
        return f"Successfully pressed hotkey combination: {' + '.join(keys)}"
    except Exception as e:
        return f"Failed to press keys: {e}"

def register(brain, settings) -> None:
    """Register GUI tools."""
    brain.register_tool(
        name="mouse_move",
        description="Moves the mouse cursor to the specified absolute X and Y coordinates on the screen.",
        parameters={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "The X coordinate"},
                "y": {"type": "integer", "description": "The Y coordinate"}
            },
            "required": ["x", "y"]
        },
        handler=_mouse_move
    )
    
    brain.register_tool(
        name="mouse_click",
        description="Clicks the mouse at the current cursor location, or at the specified X, Y coordinates if provided.",
        parameters={
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Optional X coordinate to move to before clicking"},
                "y": {"type": "integer", "description": "Optional Y coordinate to move to before clicking"},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "description": "Which mouse button to click (default: left)"},
                "clicks": {"type": "integer", "description": "Number of clicks (default: 1, set to 2 for double click)"}
            }
        },
        handler=_mouse_click
    )
    
    brain.register_tool(
        name="keyboard_type",
        description="Types the provided text string using the keyboard, as if a human was typing it.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to type"},
                "interval": {"type": "number", "description": "Optional delay between keystrokes in seconds (default: 0.05)"}
            },
            "required": ["text"]
        },
        handler=_keyboard_type
    )
    
    brain.register_tool(
        name="keyboard_press",
        description="Presses a specific hotkey or combination of keys (e.g. 'enter', 'ctrl', 'c').",
        parameters={
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of keys to press together (e.g. ['ctrl', 'c'] or ['enter'])"
                }
            },
            "required": ["keys"]
        },
        handler=_keyboard_press
    )
    
    logger.info("Computer Control (PyAutoGUI) plugin registered.")
