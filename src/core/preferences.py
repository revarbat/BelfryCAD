"""
Preferences management for PyTkCAD.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import AppConfig
from ..utils.logger import get_logger

class PreferencesManager:
    """Manages application preferences."""

    def __init__(self, config: AppConfig):
        """Initialize preferences manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.preferences: Dict[str, Any] = config.default_prefs.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value.

        Args:
            key: Preference key
            default: Default value if key not found

        Returns:
            Preference value
        """
        return self.preferences.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a preference value.

        Args:
            key: Preference key
            value: Preference value
        """
        self.preferences[key] = value

    def load(self) -> None:
        """Load preferences from file."""
        try:
            if self.config.prefs_file.exists():
                with open(self.config.prefs_file, 'r') as f:
                    loaded_prefs = json.load(f)

                # Update preferences with loaded values
                self.preferences.update(loaded_prefs)

                self.logger.info(f"Loaded preferences from {self.config.prefs_file}")
            else:
                self.logger.info("No preferences file found, using defaults")

        except Exception as e:
            self.logger.error(f"Error loading preferences: {e}")
            # Continue with default preferences

    def save(self) -> None:
        """Save preferences to file."""
        try:
            # Ensure preferences directory exists
            self.config.prefs_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config.prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)

            self.logger.info(f"Saved preferences to {self.config.prefs_file}")

        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")

    def reset_to_defaults(self) -> None:
        """Reset all preferences to default values."""
        self.preferences = self.config.default_prefs.copy()
        self.logger.info("Reset preferences to defaults")
