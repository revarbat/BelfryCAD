"""
Preferences Model for BelfryCAD.

This model contains pure business logic for preference management,
with no UI dependencies.
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

try:
    from ..config import AppConfig
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path as PathLib
    sys.path.append(str(PathLib(__file__).parent.parent))
    from config import AppConfig
    from utils.logger import get_logger


class PreferencesModel:
    """
    Pure preferences model with business logic only.
    
    This model handles:
    - Preference storage and retrieval
    - File I/O operations
    - Validation and defaults
    - No UI concerns or signals
    """
    
    def __init__(self, config: AppConfig):
        """Initialize preferences model.
        
        Args:
            config: Application configuration containing defaults and file paths
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self._preferences: Dict[str, Any] = {}
        self._defaults = self._get_default_preferences()
        
        # Initialize with defaults
        self.reset_to_defaults()
        
        self.logger.info(f"Preferences model initialized with {len(self._defaults)} default preferences")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value.
        
        Args:
            key: Preference key
            default: Default value if key not found
            
        Returns:
            Preference value or default
        """
        if key in self._preferences:
            value = self._preferences[key]
        elif key in self._defaults:
            value = self._defaults[key]
        else:
            value = default
            
        self.logger.debug(f"Getting preference '{key}': {value}")
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set a preference value.
        
        Args:
            key: Preference key
            value: Preference value
            
        Returns:
            True if value was changed, False if it was the same
        """
        old_value = self._preferences.get(key)
        
        # Validate the value
        if not self._validate_preference(key, value):
            self.logger.warning(f"Invalid value for preference '{key}': {value}")
            return False
        
        if old_value != value:
            self.logger.debug(f"Setting preference '{key}': {old_value} -> {value}")
            self._preferences[key] = value
            return True
        
        return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all preferences as a dictionary copy."""
        return self._preferences.copy()
    
    def set_multiple(self, preferences: Dict[str, Any]) -> List[str]:
        """Set multiple preferences at once.
        
        Args:
            preferences: Dictionary of preference key-value pairs
            
        Returns:
            List of keys that were actually changed
        """
        changed_keys = []
        for key, value in preferences.items():
            if self.set(key, value):
                changed_keys.append(key)
        return changed_keys
    
    def get_default(self, key: str) -> Any:
        """Get the default value for a preference key.
        
        Args:
            key: Preference key
            
        Returns:
            Default value or None if key doesn't exist
        """
        return self._defaults.get(key)
    
    def get_all_defaults(self) -> Dict[str, Any]:
        """Get all default preferences."""
        return self._defaults.copy()
    
    def reset_to_default(self, key: str) -> bool:
        """Reset a single preference to its default value.
        
        Args:
            key: Preference key to reset
            
        Returns:
            True if value was changed, False otherwise
        """
        if key in self._defaults:
            return self.set(key, self._defaults[key])
        else:
            self.logger.warning(f"No default value for preference '{key}'")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset all preferences to their default values."""
        self._preferences = self._defaults.copy()
        self.logger.info("Reset all preferences to defaults")
    
    def load_from_file(self, file_path: Optional[Path] = None) -> bool:
        """Load preferences from file.
        
        Args:
            file_path: Optional custom file path, uses config default if None
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if file_path is None:
            file_path = self.config.prefs_file
            
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    loaded_prefs = json.load(f)
                
                # Validate and update preferences
                valid_prefs = {}
                for key, value in loaded_prefs.items():
                    if self._validate_preference(key, value):
                        valid_prefs[key] = value
                    else:
                        self.logger.warning(f"Skipping invalid preference '{key}': {value}")
                
                self._preferences.update(valid_prefs)
                
                self.logger.info(f"Loaded {len(valid_prefs)} preferences from {file_path}")
                return True
            else:
                self.logger.info(f"No preferences file found at {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading preferences from {file_path}: {e}")
            return False
    
    def save_to_file(self, file_path: Optional[Path] = None) -> bool:
        """Save preferences to file.
        
        Args:
            file_path: Optional custom file path, uses config default if None
            
        Returns:
            True if saved successfully, False otherwise
        """
        if file_path is None:
            file_path = self.config.prefs_file
            
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(self._preferences, f, indent=2, sort_keys=True)
            
            self.logger.info(f"Saved {len(self._preferences)} preferences to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving preferences to {file_path}: {e}")
            return False
    
    def export_preferences(self, file_path: Path) -> bool:
        """Export preferences to a custom file location.
        
        Args:
            file_path: File path to export to
            
        Returns:
            True if exported successfully, False otherwise
        """
        return self.save_to_file(file_path)
    
    def import_preferences(self, file_path: Path) -> bool:
        """Import preferences from a custom file location.
        
        Args:
            file_path: File path to import from
            
        Returns:
            True if imported successfully, False otherwise
        """
        return self.load_from_file(file_path)
    
    def get_preference_keys(self) -> List[str]:
        """Get all preference keys (both set and default)."""
        all_keys = set(self._preferences.keys()) | set(self._defaults.keys())
        return sorted(list(all_keys))
    
    def has_preference(self, key: str) -> bool:
        """Check if a preference key exists.
        
        Args:
            key: Preference key
            
        Returns:
            True if preference exists (either set or has default)
        """
        return key in self._preferences or key in self._defaults
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default preferences from config."""
        return self.config.default_prefs.copy()
    
    def _validate_preference(self, key: str, value: Any) -> bool:
        """Validate a preference value.
        
        Args:
            key: Preference key
            value: Value to validate
            
        Returns:
            True if value is valid, False otherwise
        """
        # Basic validation - can be extended with more sophisticated rules
        
        # Check if key is known (has a default or is already set)
        if not (key in self._defaults or key in self._preferences):
            # Allow new preferences for extensibility
            return True
        
        # Type validation based on default value
        default_value = self._defaults.get(key)
        if default_value is not None:
            expected_type = type(default_value)
            if not isinstance(value, expected_type):
                # Special case: allow int/float conversion
                if expected_type in (int, float) and isinstance(value, (int, float)):
                    return True
                else:
                    return False
        
        # Additional validation rules can go here
        
        return True 