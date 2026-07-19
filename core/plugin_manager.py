"""
JARVIS Plugin Manager

Dynamically loads all plugins in the configured plugin directory
and registers their tools with the Brain.
"""

import importlib
import inspect
import os
import sys
from pathlib import Path

from core.config import Settings
from core.logger import get_logger

logger = get_logger("plugins")


class PluginManager:
    """Manages discovery and loading of JARVIS plugins."""

    def __init__(self, settings: Settings, brain):
        self._settings = settings
        self._brain = brain
        self._plugin_dir = Path(settings.plugins.plugin_dir).resolve()
        
    def load_all(self):
        """Discover and load all plugins in the plugin directory."""
        if not self._settings.plugins.enabled:
            logger.info("Plugins are disabled in settings.")
            return

        if not self._plugin_dir.exists() or not self._plugin_dir.is_dir():
            logger.warning(f"Plugin directory not found: {self._plugin_dir}")
            return

        # Add the parent directory of plugins to sys.path so we can import them
        parent_dir = str(self._plugin_dir.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            
        plugin_count = 0
        
        for file in self._plugin_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
                
            module_name = f"{self._plugin_dir.name}.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                # Look for a register() function
                if hasattr(module, "register") and inspect.isfunction(module.register):
                    module.register(self._brain, self._settings)
                    plugin_count += 1
                    logger.debug(f"Loaded plugin: {module_name}")
                else:
                    logger.debug(f"Plugin {module_name} has no register() function, skipping.")
            except Exception as e:
                logger.error(f"Failed to load plugin {module_name}: {e}", exc_info=True)
                
        logger.info(f"Loaded {plugin_count} plugins.")
