"""
Preferences ViewModel for BelfryCAD.

This ViewModel manages application preferences using the MVVM pattern,
providing signals for UI updates when preferences change and delegating
business logic to the PreferencesModel.
"""

from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal

from ...models.preferences import PreferencesModel
from ...config import AppConfig


class PreferencesViewModel(QObject):
    """Presentation logic for preferences with signals"""
    
    # Preference signals
    preference_changed = Signal(str, object)  # key, value
    preferences_loaded = Signal()
    preferences_saved = Signal()
    preferences_reset = Signal()
    
    # Category-specific signals
    display_preferences_changed = Signal()
    grid_preferences_changed = Signal()
    snap_preferences_changed = Signal()
    tool_preferences_changed = Signal()
    file_preferences_changed = Signal()
    window_preferences_changed = Signal()
    performance_preferences_changed = Signal()
    
    def __init__(self, preferences_model: PreferencesModel):
        """Initialize preferences ViewModel.
        
        Args:
            preferences_model: The preferences model to delegate to
        """
        super().__init__()
        self._model = preferences_model
        self._categories = self._get_preference_categories()
    
    @property
    def model(self) -> PreferencesModel:
        """Get the underlying preferences model."""
        return self._model
    
    def get(self, key: str, default=None):
        """Get a preference value"""
        return self._model.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a preference value"""
        if self._model.set(key, value):
            self.preference_changed.emit(key, value)
            
            # Emit category-specific signals
            category = self._get_preference_category(key)
            if category:
                self._emit_category_signal(category)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all preferences"""
        return self._model.get_all()
    
    def set_multiple(self, preferences: Dict[str, Any]) -> List[str]:
        """Set multiple preferences at once"""
        changed_keys = self._model.set_multiple(preferences)
        
        # Emit signals for changed preferences
        categories_changed = set()
        for key in changed_keys:
            self.preference_changed.emit(key, self._model.get(key))
            category = self._get_preference_category(key)
            if category:
                categories_changed.add(category)
        
        # Emit category signals
        for category in categories_changed:
            self._emit_category_signal(category)
        
        return changed_keys
    
    def get_default(self, key: str):
        """Get default value for a preference"""
        return self._model.get_default(key)
    
    def get_all_defaults(self) -> Dict[str, Any]:
        """Get all default preferences"""
        return self._model.get_all_defaults()
    
    def reset_to_default(self, key: str):
        """Reset a preference to its default value"""
        if self._model.reset_to_default(key):
            value = self._model.get(key)
            self.preference_changed.emit(key, value)
            
            category = self._get_preference_category(key)
            if category:
                self._emit_category_signal(category)
    
    def reset_all_to_defaults(self):
        """Reset all preferences to default values"""
        self._model.reset_to_defaults()
        self.preferences_reset.emit()
        self.preferences_loaded.emit()
        
        # Emit all category signals
        for category in self.get_categories():
            self._emit_category_signal(category)
    
    def load_preferences(self) -> bool:
        """Load preferences from file"""
        if self._model.load_from_file():
            self.preferences_loaded.emit()
            
            # Emit all category signals since multiple preferences may have changed
            for category in self.get_categories():
                self._emit_category_signal(category)
            
            return True
        return False
    
    def save_preferences(self) -> bool:
        """Save preferences to file"""
        if self._model.save_to_file():
            self.preferences_saved.emit()
            return True
        return False
    
    def export_preferences(self, file_path: str) -> bool:
        """Export preferences to a file"""
        from pathlib import Path
        return self._model.export_preferences(Path(file_path))
    
    def import_preferences(self, file_path: str) -> bool:
        """Import preferences from a file"""
        from pathlib import Path
        if self._model.import_preferences(Path(file_path)):
            self.preferences_loaded.emit()
            
            # Emit all category signals
            for category in self.get_categories():
                self._emit_category_signal(category)
            
            return True
        return False
    
    def get_preferences_by_category(self, category: str) -> Dict[str, Any]:
        """Get preferences for a specific category"""
        category_prefs = {}
        keys = self.get_category_keys(category)
        for key in keys:
            category_prefs[key] = self.get(key)
        return category_prefs
    
    def get_categories(self) -> List[str]:
        """Get all preference categories"""
        return list(self._categories.keys())
    
    def get_category_description(self, category: str) -> str:
        """Get description for a preference category"""
        return self._categories.get(category, {}).get('description', '')
    
    def get_category_keys(self, category: str) -> List[str]:
        """Get preference keys for a specific category"""
        return self._categories.get(category, {}).get('keys', [])
    
    def has_preference(self, key: str) -> bool:
        """Check if a preference exists"""
        return self._model.has_preference(key)
    
    def get_preference_keys(self) -> List[str]:
        """Get all preference keys"""
        return self._model.get_preference_keys()
    
    # Display preferences convenience methods
    def get_show_grid(self) -> bool:
        """Get show grid preference"""
        return self.get('grid_visible', True)
    
    def set_show_grid(self, show: bool):
        """Set show grid preference"""
        self.set('grid_visible', show)
    
    def get_grid_color(self) -> str:
        """Get grid color preference"""
        return self.get('grid_color', '#CCCCCC')
    
    def set_grid_color(self, color: str):
        """Set grid color preference"""
        self.set('grid_color', color)
    
    def get_background_color(self) -> str:
        """Get background color preference"""
        return self.get('canvas_bg_color', '#FFFFFF')
    
    def set_background_color(self, color: str):
        """Set background color preference"""
        self.set('canvas_bg_color', color)
    
    def get_show_rulers(self) -> bool:
        """Get show rulers preference"""
        return self.get('show_rulers', True)
    
    def set_show_rulers(self, show: bool):
        """Set show rulers preference"""
        self.set('show_rulers', show)
    
    # File preferences convenience methods
    def get_auto_save_enabled(self) -> bool:
        """Get auto-save enabled preference"""
        return self.get('auto_save', False)
    
    def set_auto_save_enabled(self, enabled: bool):
        """Set auto-save enabled preference"""
        self.set('auto_save', enabled)
    
    def get_auto_save_interval(self) -> int:
        """Get auto-save interval preference"""
        return self.get('auto_save_interval', 300)
    
    def set_auto_save_interval(self, interval: int):
        """Set auto-save interval preference"""
        self.set('auto_save_interval', interval)
    
    def get_recent_files_count(self) -> int:
        """Get recent files count preference"""
        return self.get('recent_files_count', 10)
    
    def set_recent_files_count(self, count: int):
        """Set recent files count preference"""
        self.set('recent_files_count', count)
    
    # Window preferences convenience methods
    def get_window_geometry(self) -> str:
        """Get window geometry preference"""
        return self.get('window_geometry', '')
    
    def set_window_geometry(self, geometry: str):
        """Set window geometry preference"""
        self.set('window_geometry', geometry)
    
    def get_units(self) -> str:
        """Get units preference"""
        return self.get('units', 'inches')
    
    def set_units(self, units: str):
        """Set units preference"""
        self.set('units', units)
    
    def get_precision(self) -> int:
        """Get precision preference"""
        return self.get('precision', 3)
    
    def set_precision(self, precision: int):
        """Set precision preference"""
        self.set('precision', precision)
    
    def _get_preference_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get preference categories and their descriptions"""
        return {
            'display': {
                'description': 'Display and appearance settings',
                'keys': ['grid_visible', 'show_rulers', 'canvas_bg_color', 'grid_color', 'selection_color']
            },
            'file': {
                'description': 'File and document settings',
                'keys': ['auto_save', 'auto_save_interval', 'recent_files_count']
            },
            'window': {
                'description': 'Window and interface settings',
                'keys': ['window_geometry']
            },
            'units': {
                'description': 'Units and precision settings',
                'keys': ['units', 'precision']
            }
        }
    
    def _get_preference_category(self, key: str) -> Optional[str]:
        """Get the category for a preference key"""
        for category, info in self._categories.items():
            if key in info.get('keys', []):
                return category
        return None
    
    def _emit_category_signal(self, category: str):
        """Emit category-specific signal"""
        if category == 'display':
            self.display_preferences_changed.emit()
        elif category == 'file':
            self.file_preferences_changed.emit()
        elif category == 'window':
            self.window_preferences_changed.emit()
        elif category == 'performance':
            self.performance_preferences_changed.emit() 