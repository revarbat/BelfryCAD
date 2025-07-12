# Preferences System MVVM Conversion

## Overview

The preferences system has been successfully converted from a mixed architecture to a proper MVVM (Model-View-ViewModel) design pattern. This conversion provides better separation of concerns, improved testability, and cleaner code organization.

## Architecture Components

### 1. Model Layer (`src/BelfryCAD/models/preferences.py`)

**PreferencesModel**: Pure business logic for preference management
- Handles preference storage and retrieval
- Manages file I/O operations
- Provides validation and defaults
- No UI dependencies or signals

Key features:
- Validates preference values based on type
- Supports import/export of preferences
- Provides atomic operations for multiple preference changes
- Comprehensive error handling and logging

```python
from BelfryCAD.models.preferences import PreferencesModel
from BelfryCAD.config import AppConfig

# Create model
config = AppConfig()
model = PreferencesModel(config)

# Basic operations
value = model.get('grid_visible', True)
changed = model.set('grid_visible', False)
model.save_to_file()
```

### 2. ViewModel Layer (`src/BelfryCAD/gui/viewmodels/preferences_viewmodel.py`)

**PreferencesViewModel**: Presentation logic with Qt signals
- Delegates business logic to PreferencesModel
- Emits signals for UI updates
- Organizes preferences by categories
- Provides convenience methods for common preferences

Key features:
- Real-time signal emission on preference changes
- Category-specific signals for fine-grained updates
- Convenience methods for common preferences
- Support for batch operations

```python
from BelfryCAD.gui.viewmodels.preferences_viewmodel import PreferencesViewModel
from BelfryCAD.models.preferences import PreferencesModel

# Create ViewModel
model = PreferencesModel(config)
viewmodel = PreferencesViewModel(model)

# Connect to signals
viewmodel.preference_changed.connect(on_preference_changed)
viewmodel.display_preferences_changed.connect(on_display_changed)

# Use convenience methods
viewmodel.set_show_grid(True)
grid_color = viewmodel.get_grid_color()
```

### 3. View Layer (`src/BelfryCAD/gui/views/preferences_dialog.py`)

**PreferencesDialog**: Pure UI that delegates to ViewModel
- Contains only UI logic
- Delegates all business logic to ViewModel
- Responds to ViewModel signals
- Provides various preference control widgets

Key features:
- Tabbed interface organized by preference categories
- Various control types (boolean, integer, string, combo, color)
- Real-time updates from ViewModel signals
- Import/export functionality

```python
from BelfryCAD.gui.views.preferences_dialog import PreferencesDialog

# Show dialog
dialog = PreferencesDialog(preferences_viewmodel, parent)
result = dialog.exec()
```

## Preference Categories

The system organizes preferences into logical categories:

### Display
- `grid_visible`: Show/hide grid
- `show_rulers`: Show/hide rulers  
- `canvas_bg_color`: Background color
- `grid_color`: Grid line color
- `selection_color`: Selection highlight color

### Snap
- `snap_to_grid`: Enable grid snapping

### File  
- `auto_save`: Enable automatic saving
- `auto_save_interval`: Auto-save interval in seconds
- `recent_files_count`: Number of recent files to remember

### Units
- `units`: Default units (inches/mm)
- `precision`: Decimal precision for display

### Window
- `window_geometry`: Window size and position

## Backward Compatibility

The conversion maintains full backward compatibility:

### Legacy PreferencesManager
The old `PreferencesManager` in `src/BelfryCAD/core/preferences.py` now bridges to the new MVVM system:

```python
# Old code continues to work
from BelfryCAD.core.preferences import PreferencesManager

prefs = PreferencesManager(config)
prefs.set('grid_visible', True)
prefs.save()
```

### Legacy Preferences Dialog
The old dialog in `src/BelfryCAD/gui/dialogs/preferences_dialog.py` now delegates to the new MVVM dialog:

```python
# Old code continues to work
from BelfryCAD.gui.dialogs.preferences_dialog import show_preferences_dialog

dialog = show_preferences_dialog(parent)
```

## Usage Examples

### Basic Usage

```python
from BelfryCAD.config import AppConfig
from BelfryCAD.models.preferences import PreferencesModel
from BelfryCAD.gui.viewmodels.preferences_viewmodel import PreferencesViewModel
from BelfryCAD.gui.views.preferences_dialog import PreferencesDialog

# Create components
config = AppConfig()
model = PreferencesModel(config)
viewmodel = PreferencesViewModel(model)

# Load preferences
viewmodel.load_preferences()

# Show dialog
dialog = PreferencesDialog(viewmodel, parent)
dialog.exec()
```

### Integration with MainWindow

```python
class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        
        # Create preferences system
        self.preferences_model = PreferencesModel(config)
        self.preferences_viewmodel = PreferencesViewModel(self.preferences_model)
        self.preferences_viewmodel.load_preferences()
        
        # Connect to preference changes
        self.preferences_viewmodel.display_preferences_changed.connect(
            self._on_display_preferences_changed)
        
        # Apply current preferences
        self._apply_preferences()
    
    def _show_preferences(self):
        """Show preferences dialog"""
        dialog = PreferencesDialog(self.preferences_viewmodel, self)
        dialog.exec()
    
    def _apply_preferences(self):
        """Apply preferences to UI"""
        # Apply display preferences
        show_grid = self.preferences_viewmodel.get_show_grid()
        bg_color = self.preferences_viewmodel.get_background_color()
        # Update UI based on preferences
    
    def _on_display_preferences_changed(self):
        """Handle display preference changes"""
        self._apply_preferences()
```

### Custom Preference Controls

```python
from BelfryCAD.gui.views.preferences_dialog import PreferenceControlWidget

class CustomPreferenceControl(PreferenceControlWidget):
    """Custom control for specialized preferences"""
    
    def _create_widget(self):
        # Create custom UI
        pass
    
    def get_value(self):
        # Return current value
        pass
    
    def set_value(self, value):
        # Set widget value
        pass
```

## Signal Flow

The MVVM architecture ensures clean signal flow:

1. **User Interaction**: User modifies preference in dialog
2. **View → ViewModel**: Dialog calls ViewModel setter method
3. **ViewModel → Model**: ViewModel delegates to Model
4. **Model Validation**: Model validates and stores value
5. **ViewModel Signals**: ViewModel emits preference_changed signal
6. **UI Updates**: Connected UI components update automatically

## Benefits

### Separation of Concerns
- **Model**: Pure business logic, no UI dependencies
- **ViewModel**: Presentation logic with signals, no UI widgets
- **View**: Pure UI logic, no business logic

### Testability
- Models can be tested without UI framework
- ViewModels can be tested with mock models
- Views can be tested with mock ViewModels

### Maintainability
- Clear responsibilities for each component
- Easy to modify or extend individual layers
- Consistent patterns across the application

### Real-time Updates
- Automatic UI updates when preferences change
- Category-specific signals for efficient updates
- Support for external preference modifications

## File Structure

```
src/BelfryCAD/
├── models/
│   └── preferences.py              # PreferencesModel (business logic)
├── gui/
│   ├── viewmodels/
│   │   └── preferences_viewmodel.py   # PreferencesViewModel (signals)
│   ├── views/
│   │   └── preferences_dialog.py      # PreferencesDialog (pure UI)
│   └── dialogs/
│       └── preferences_dialog.py      # Legacy bridge
└── core/
    └── preferences.py              # Legacy PreferencesManager bridge
```

## Testing

The MVVM architecture enables comprehensive testing:

```python
def test_preferences_model():
    """Test model business logic"""
    config = AppConfig()
    model = PreferencesModel(config)
    
    # Test validation
    assert model.set('grid_visible', True) == True
    assert model.set('grid_visible', 'invalid') == False
    
    # Test file operations
    assert model.save_to_file() == True

def test_preferences_viewmodel():
    """Test ViewModel signals"""
    model = Mock()
    viewmodel = PreferencesViewModel(model)
    
    # Test signal emission
    with patch.object(viewmodel, 'preference_changed') as mock_signal:
        viewmodel.set('grid_visible', True)
        mock_signal.emit.assert_called_with('grid_visible', True)
```

## Migration Guide

For existing code using the old preferences system:

1. **No immediate changes required** - backward compatibility is maintained
2. **Gradual migration** - Update components to use new ViewModel as convenient
3. **New features** - Use MVVM architecture for all new preference-related features

## Conclusion

The preferences system MVVM conversion provides a solid foundation for preference management that is:
- Well-architected with clear separation of concerns
- Fully backward compatible
- Easily testable and maintainable
- Extensible for future enhancements

This conversion serves as a template for migrating other BelfryCAD systems to MVVM architecture. 