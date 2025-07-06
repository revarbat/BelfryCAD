"""
Preferences management for BelfryCad.
"""

import json
from typing import Any, Dict
import logging

try:
    from ..config import AppConfig
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config import AppConfig
    from utils.logger import get_logger


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
        self.logger.info(f"Initialized preferences with defaults: {self.preferences}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value.

        Args:
            key: Preference key
            default: Default value if key not found

        Returns:
            Preference value
        """
        value = self.preferences.get(key, default)
        self.logger.debug(f"Getting preference '{key}': {value}")
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a preference value.

        Args:
            key: Preference key
            value: Preference value
        """
        self.logger.debug(f"Setting preference '{key}': {value}")
        self.preferences[key] = value

    def load(self) -> None:
        """Load preferences from file."""
        try:
            if self.config.prefs_file.exists():
                with open(self.config.prefs_file, 'r') as f:
                    loaded_prefs = json.load(f)

                # Update preferences with loaded values
                self.preferences.update(loaded_prefs)

                self.logger.info(
                    f"Loaded preferences from {self.config.prefs_file}: {loaded_prefs}")
            else:
                self.logger.info(f"No preferences file found at {self.config.prefs_file}, using defaults")

        except Exception as e:
            self.logger.error(f"Error loading preferences from {self.config.prefs_file}: {e}")
            # Continue with default preferences

    def save(self) -> None:
        """Save preferences to file."""
        try:
            # Ensure preferences directory exists
            self.config.prefs_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config.prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)

            self.logger.info(f"Saved preferences to {self.config.prefs_file}: {self.preferences}")

        except Exception as e:
            self.logger.error(f"Error saving preferences to {self.config.prefs_file}: {e}")

    def reset_to_defaults(self) -> None:
        """Reset all preferences to default values."""
        self.preferences = self.config.default_prefs.copy()
        self.logger.info("Reset preferences to defaults")
