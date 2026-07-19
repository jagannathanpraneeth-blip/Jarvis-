"""
JARVIS Camera Vision Plugin

Allows JARVIS to access the webcam, capture an image, and use Gemini 2.0 Flash
to analyze the visual feed.
"""

import os
import cv2
from google import genai
from core.logger import get_logger

logger = get_logger("plugin.camera")


def capture_and_analyze_camera(prompt: str) -> str:
    """
    Captures a frame from the primary webcam and asks Gemini to analyze it.
    
    Args:
        prompt: What JARVIS wants to know about the image (e.g. "What is the user holding?")
    """
    logger.info("Accessing webcam...")
    
    # Initialize the camera (0 is usually the built-in webcam)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return "ERROR: Could not open the webcam. The hardware may be missing or locked."
        
    # Give the camera a second to adjust to lighting (read a few dummy frames)
    for _ in range(5):
        cap.read()
        
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return "ERROR: Failed to capture an image from the webcam."
        
    # Save the frame to a temporary file
    os.makedirs("temp", exist_ok=True)
    img_path = os.path.join("temp", "camera_capture.jpg")
    cv2.imwrite(img_path, frame)
    logger.info(f"Webcam frame captured and saved to {img_path}")
    
    # Analyze with Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "":
        return "ERROR: GEMINI_API_KEY is missing from .env."
        
    try:
        from PIL import Image
        img = Image.open(img_path)
        
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[prompt, img]
        )
        logger.info("Camera analysis complete.")
        return response.text
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return f"Failed to analyze the camera feed: {e}"


def setup(plugin_manager):
    """Registers the camera vision tool."""
    plugin_manager.brain.register_tool(
        name="analyze_camera_feed",
        description="Captures a photo from the user's webcam and analyzes it. Use this when the user says 'what am I holding', 'what is in front of me', or asks you to look at them.",
        parameters={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Specific question about what to look for in the image."
                }
            },
            "required": ["prompt"]
        },
        handler=capture_and_analyze_camera
    )
    logger.info("Camera Vision Plugin loaded.")
