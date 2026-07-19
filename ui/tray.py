"""
System Tray UI for JARVIS
"""

import os
import threading
import webbrowser
from PIL import Image, ImageDraw
import pystray

from core.logger import get_logger

logger = get_logger("ui.tray")


def create_default_icon() -> Image.Image:
    """Creates a basic JARVIS icon if one doesn't exist."""
    # Create a 64x64 transparent image
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    # Draw a blue outer ring
    dc.ellipse((4, 4, 60, 60), outline=(0, 150, 255, 255), width=4)
    # Draw a glowing core
    dc.ellipse((16, 16, 48, 48), fill=(0, 200, 255, 255))
    
    return image


class TrayApp:
    def __init__(self, settings):
        self.settings = settings
        self.icon = None
        self._thread = None
        
        # We will use this to track mute state
        self.is_muted = False
        
    def _on_dashboard(self, icon, item):
        logger.info("Opening dashboard from tray...")
        webbrowser.open("http://127.0.0.1:8000")
        
    def _on_toggle_mute(self, icon, item):
        self.is_muted = not self.is_muted
        # Update settings so VoiceLoop knows (if running)
        # Assuming VoiceLoop reads settings.voice.muted
        if hasattr(self.settings, 'voice'):
            # Dynamically add muted attribute if it doesn't exist
            self.settings.voice.muted = self.is_muted
        logger.info(f"JARVIS Muted: {self.is_muted}")
        # Re-render menu to update the checkmark
        self._update_menu()
        
    def _on_quit(self, icon, item):
        logger.info("Quit requested from tray.")
        self.stop()
        # Force terminate the whole process
        os._exit(0)
        
    def _update_menu(self):
        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", self._on_dashboard, default=True),
            pystray.MenuItem(
                "Mute JARVIS", 
                self._on_toggle_mute, 
                checked=lambda item: self.is_muted
            ),
            pystray.MenuItem("Quit", self._on_quit)
        )
        if self.icon:
            self.icon.menu = menu

    def _run_icon(self):
        logger.info("Starting System Tray icon...")
        image = create_default_icon()
        
        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", self._on_dashboard, default=True),
            pystray.MenuItem("Mute JARVIS", self._on_toggle_mute, checked=lambda item: self.is_muted),
            pystray.MenuItem("Quit", self._on_quit)
        )
        
        self.icon = pystray.Icon("JARVIS", image, "JARVIS AI Assistant", menu)
        self.icon.run()

    def start(self):
        """Starts the tray app in a background thread."""
        self._thread = threading.Thread(target=self._run_icon, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stops the tray app."""
        if self.icon:
            self.icon.stop()
            self.icon = None
