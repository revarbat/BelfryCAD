"""
Preferences Model for BelfryCAD.

This model contains pure business logic for preference management,
with no UI dependencies.
"""

import yaml
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
            value: New value
            
        Returns:
            True if value was set successfully, False if validation failed
        """
        if self._validate_preference(key, value):
            old_value = self._preferences.get(key)
            self._preferences[key] = value
            self.logger.debug(f"Setting preference '{key}': {old_value} -> {value}")
            return True
        else:
            self.logger.warning(f"Invalid preference value for '{key}': {value}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all current preferences (excluding defaults not explicitly set).
        
        Returns:
            Dictionary of all set preferences
        """
        return dict(self._preferences)
    
    def get_all_with_defaults(self) -> Dict[str, Any]:
        """Get all preferences including defaults.
        
        Returns:
            Dictionary merging defaults with set preferences
        """
        merged = dict(self._defaults)
        merged.update(self._preferences)
        return merged
    
    def reset_to_defaults(self):
        """Reset all preferences to their default values."""
        self._preferences.clear()
        self._preferences.update(self._defaults)
        self.logger.info("Reset all preferences to defaults")
    
    def reset_preference(self, key: str) -> bool:
        """Reset a single preference to its default value.
        
        Args:
            key: Preference key to reset
            
        Returns:
            True if preference was reset, False if key not found in defaults
        """
        if key in self._defaults:
            old_value = self._preferences.get(key)
            self._preferences[key] = self._defaults[key]
            self.logger.info(f"Reset preference '{key}': {old_value} -> {self._defaults[key]}")
            return True
        else:
            self.logger.warning(f"Cannot reset unknown preference: {key}")
            return False
    
    def delete_preference(self, key: str) -> bool:
        """Delete a preference (will fall back to default).
        
        Args:
            key: Preference key to delete
            
        Returns:
            True if preference was deleted, False if key not found
        """
        if key in self._preferences:
            del self._preferences[key]
            self.logger.info(f"Deleted preference: {key}")
            return True
        else:
            self.logger.warning(f"Cannot delete non-existent preference: {key}")
            return False

    
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
                    loaded_prefs = yaml.safe_load(f) or {}
                
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
                # Check for legacy JSON file and migrate if it exists
                legacy_file = file_path.parent / "preferences.json"
                if legacy_file.exists():
                    self.logger.info(f"Found legacy JSON preferences file, migrating to YAML")
                    return self._migrate_from_json(legacy_file, file_path)
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
                yaml.safe_dump(self._preferences, f, indent=2, sort_keys=True, default_flow_style=False)
            
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
    
    def _migrate_from_json(self, json_file: Path, yaml_file: Path) -> bool:
        """Migrate preferences from JSON to YAML format.
        
        Args:
            json_file: Path to the existing JSON preferences file
            yaml_file: Path to the new YAML preferences file
            
        Returns:
            True if migration was successful, False otherwise
        """
        try:
            import json
            
            # Load the JSON file
            with open(json_file, 'r') as f:
                json_prefs = json.load(f)
            
            # Validate and update preferences
            valid_prefs = {}
            for key, value in json_prefs.items():
                if self._validate_preference(key, value):
                    valid_prefs[key] = value
                else:
                    self.logger.warning(f"Skipping invalid preference during migration '{key}': {value}")
            
            self._preferences.update(valid_prefs)
            
            # Save to YAML format
            if self.save_to_file(yaml_file):
                self.logger.info(f"Successfully migrated {len(valid_prefs)} preferences from JSON to YAML")
                
                # Optionally rename the old JSON file as backup
                backup_file = json_file.parent / "preferences.json.backup"
                try:
                    json_file.rename(backup_file)
                    self.logger.info(f"Created backup of old JSON file: {backup_file}")
                except Exception as e:
                    self.logger.warning(f"Could not create backup of JSON file: {e}")
                
                return True
            else:
                self.logger.error("Failed to save preferences to YAML after migration")
                return False
                
        except Exception as e:
            self.logger.error(f"Error migrating preferences from JSON to YAML: {e}")
            return False
    
    def get_preference_keys(self) -> List[str]:
        """Get all preference keys (both set and default)."""
        all_keys = set(self._preferences.keys()) | set(self._defaults.keys())
        return sorted(list(all_keys))
    
    def has_preference(self, key: str) -> bool:
        """Check if a preference key exists (either set or has default).
        
        Args:
            key: Preference key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return key in self._preferences or key in self._defaults
    
    def is_default_value(self, key: str) -> bool:
        """Check if a preference is currently set to its default value.
        
        Args:
            key: Preference key to check
            
        Returns:
            True if current value equals default, False otherwise
        """
        if key not in self._defaults:
            return False
        
        current_value = self.get(key)
        default_value = self._defaults[key]
        return current_value == default_value
    
    def get_modified_preferences(self) -> Dict[str, Any]:
        """Get only preferences that differ from their defaults.
        
        Returns:
            Dictionary of modified preferences
        """
        modified = {}
        for key, value in self._preferences.items():
            if key in self._defaults:
                if value != self._defaults[key]:
                    modified[key] = value
            else:
                # No default exists, so it's a custom preference
                modified[key] = value
        
        return modified
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get the default preferences from config.
        
        Returns:
            Dictionary of default preferences
        """
        return dict(self.config.default_prefs)
    
    def _validate_preference(self, key: str, value: Any) -> bool:
        """Validate a preference key and value.
        
        Args:
            key: Preference key
            value: Preference value
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - can be extended for specific preference rules
        if not isinstance(key, str) or not key.strip():
            return False
        
        # Type-specific validation for known preferences
        if key == "precision" and not isinstance(value, int):
            return False
        if key == "auto_save_interval" and not isinstance(value, int):
            return False
        if key == "recent_files_count" and not isinstance(value, int):
            return False
        if key in ["grid_visible", "show_rulers", "auto_save"] and not isinstance(value, bool):
            return False
        if key == "recent_files" and not isinstance(value, list):
            return False
        
        return True
