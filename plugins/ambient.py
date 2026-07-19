"""
Ambient Context Plugin for JARVIS

Provides tools for JARVIS to understand the user's current context
without needing explicit explanations (Clipboard, Active Window, Screenshots).
Uses Google Gemini for visual analysis.
"""

import io
import os
import base64
from typing import Any

import pyperclip
import pygetwindow as gw
import pyautogui
from PIL import Image

from google import genai
from google.genai import types

from core.logger import get_logger

logger = get_logger("plugin.ambient")


def register(brain, settings):
    """Registers the Ambient Context tools with the JARVIS Brain."""
    
    def read_clipboard() -> str:
        """Reads the current text from the user's clipboard."""
        try:
            content = pyperclip.paste()
            if not content:
                return "The clipboard is currently empty."
            if len(content) > 5000:
                return content[:5000] + "\n...[CLIPBOARD TRUNCATED]..."
            return content
        except Exception as e:
            return f"Error reading clipboard: {e}"

    def get_active_window() -> str:
        """Returns the title of the currently focused window."""
        try:
            window = gw.getActiveWindow()
            if window and window.title:
                return f"Active Window: {window.title}"
            return "No active window found or title is empty."
        except Exception as e:
            return f"Error getting active window: {e}"
            
    def take_screenshot() -> str:
        """Takes a screenshot and uses Gemini Vision to describe it."""
        # --- Safety Rail ---
        if not settings.plugins.god_mode:
            print(f"\n[WARNING] JARVIS wants to take a screenshot of your monitor.")
            try:
                response = input("  Allow screenshot? [y/N]: ").strip().lower()
                if response != 'y':
                    logger.info("User rejected screenshot.")
                    return "ERROR: The user rejected the screenshot request."
            except Exception as e:
                return f"ERROR: Failed to get user permission: {e}"
        # -------------------
        
        try:
            # 1. Take the screenshot
            logger.info("Capturing screenshot...")
            screenshot = pyautogui.screenshot()
            
            # Save a local copy for debugging/UI
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            filepath = os.path.join(temp_dir, "latest_screenshot.png")
            screenshot.save(filepath)
            
            # 2. Prepare image for Gemini
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            if not settings.gemini_api_key:
                return f"Screenshot saved to {filepath}. However, GEMINI_API_KEY is not configured in .env, so I cannot analyze it visually."
                
            # 3. Call Gemini Vision
            logger.info("Sending screenshot to Gemini for analysis...")
            client = genai.Client(api_key=settings.gemini_api_key)
            
            # Gemini 2.0 Flash is great for multimodal
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    "Analyze this screenshot of my computer. Describe exactly what applications are open, what text is visible, and what I seem to be doing. Be highly detailed but concise.",
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                ]
            )
            
            desc = response.text
            return f"Screenshot taken successfully.\nVisual Analysis from Gemini:\n{desc}"
            
        except Exception as e:
            logger.error(f"Screenshot/Vision error: {e}", exc_info=True)
            return f"Error taking or analyzing screenshot: {e}"

    # Register tools
    brain.register_tool(
        name="read_clipboard",
        description="Reads the current text copied to the user's clipboard. Use this when the user says 'summarize this' or 'what is copied'.",
        parameters={"type": "object", "properties": {}},
        handler=read_clipboard
    )
    
    brain.register_tool(
        name="get_active_window",
        description="Gets the title of the window the user is currently looking at. Use this to understand their context.",
        parameters={"type": "object", "properties": {}},
        handler=get_active_window
    )
    
    brain.register_tool(
        name="take_screenshot",
        description="Takes a screenshot of the user's screen and returns a detailed text description of what is visible. Use this when the user asks 'what am I looking at' or 'do you see this error'.",
        parameters={"type": "object", "properties": {}},
        handler=take_screenshot
    )
    
    logger.info("Ambient Context plugin registered.")
