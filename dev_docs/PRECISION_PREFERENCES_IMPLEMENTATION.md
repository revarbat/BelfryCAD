# Precision Preferences Implementation

## Overview

This document describes the implementation of decimal precision preferences throughout the BelfryCAD application. The precision setting now controls the number of decimal places displayed in:

1. **GridInfo formatters** - Grid labels and ruler displays
2. **ControlDatums** - Control point datum labels
3. **ConfigPane spinboxes** - Property editor float fields

## Architecture Changes

### 1. GridInfo Precision

**File**: `src/BelfryCAD/gui/grid_info.py`

- Modified `GridInfo.__init__()` to accept `decimal_places` parameter
- The `format_label()` method now uses `self._decimal_places` for formatting
- Main window creates GridInfo with precision from preferences

**Changes**:
```python
# Before
self.grid_info = GridInfo(GridUnits.INCHES_DECIMAL)

# After  
precision = self.preferences_viewmodel.get("precision", 3)
self.grid_info = GridInfo(GridUnits.INCHES_DECIMAL, decimal_places=precision)
```

### 2. ControlDatum Precision

**File**: `src/BelfryCAD/gui/views/graphics_items/control_points.py`

- Modified `ControlDatum.__init__()` to accept `precision` parameter
- Format string is now created dynamically: `f"{{:.{precision}f}}"`
- All CAD items now pass precision from scene to ControlDatum

**Changes**:
```python
# Before
def __init__(self, setter=None, format_string="{:.3f}", prefix="", suffix="", cad_item=None):

# After
def __init__(self, setter=None, format_string=None, prefix="", suffix="", cad_item=None, precision=3):
    # Use provided format_string or create one from precision
    if format_string is None:
        self.format_string = f"{{:.{precision}f}}"
    else:
        self.format_string = format_string
```

### 3. CadScene Precision Management

**File**: `src/BelfryCAD/gui/views/widgets/cad_scene.py`

- Added `precision` parameter to `__init__()`
- Added `get_precision()` and `set_precision()` methods
- CAD items can now access scene precision for ControlDatum creation

**Changes**:
```python
def __init__(self, parent=None, precision=3):
    # Store precision for CAD items to use
    self._precision = precision

def get_precision(self):
    """Get the precision setting for this scene."""
    return self._precision

def set_precision(self, precision):
    """Set the precision setting for this scene."""
    self._precision = precision
```

### 4. CAD Items Precision Integration

**Files**: All CAD item files in `src/BelfryCAD/gui/views/graphics_items/caditems/`

- Added imports for `CadScene` and `cast`
- Modified `_create_controls_impl()` to get precision from scene
- Pass precision to ControlDatum constructor

**Changes**:
```python
# Get precision from scene
precision = 3  # Default fallback
scene = self.scene()
if scene and isinstance(scene, CadScene):
    precision = scene.get_precision()

# Create ControlDatum with precision
self._radius_datum = ControlDatum(
    setter=self._set_radius_value,
    prefix="R",
    cad_item=self,
    precision=precision
)
```

### 5. ConfigPane Precision

**File**: `src/BelfryCAD/gui/panes/config_pane.py`

- Added `precision` parameter to `__init__()`
- Modified `_create_float_field()` to use `self.precision`
- Added `update_precision()` method for runtime updates
- Updated `create_config_pane()` function

**Changes**:
```python
def __init__(self, canvas=None, parent: Optional[QWidget] = None, precision=3):
    self.precision = precision

def _create_float_field(self, row: int, field: Dict[str, Any]):
    # ...
    spinbox.setDecimals(self.precision)

def update_precision(self, new_precision: int):
    """Update the precision and refresh all float fields."""
    self.precision = new_precision
    # Update all existing float spinboxes
    for widget in self.field_widgets.values():
        if isinstance(widget, QDoubleSpinBox):
            widget.setDecimals(new_precision)
```

### 6. Main Window Integration

**File**: `src/BelfryCAD/gui/main_window.py`

- Pass precision to CadScene constructor
- Handle precision preference changes
- Update GridInfo, CadScene, and ConfigPane when precision changes

**Changes**:
```python
def _create_canvas(self):
    # Get precision from preferences
    precision = self.preferences_viewmodel.get("precision", 3)
    self.grid_info = GridInfo(GridUnits.INCHES_DECIMAL, decimal_places=precision)
    self.cad_scene = CadScene(self, precision=precision)

def _on_preference_changed(self, key: str, value):
    elif key == "precision" and hasattr(self, 'grid_info'):
        # Update GridInfo precision and refresh grid display
        self.grid_info.decimal_places = value
        if hasattr(self, 'cad_scene'):
            self.cad_scene.set_precision(value)
        # ... update other components
```

### 7. Palette System Integration

**File**: `src/BelfryCAD/gui/palette_system.py`

- Modified `_create_content_widget()` to pass precision to ConfigPane
- Get precision from main window preferences

**Changes**:
```python
elif palette_type == PaletteType.CONFIG_PANE:
    # Get precision from main window preferences
    precision = 3  # Default fallback
    if hasattr(self.main_window, 'preferences_viewmodel'):
        precision = self.main_window.preferences_viewmodel.get("precision", 3)
    return ConfigPane(precision=precision)
```

## Files Modified

1. `src/BelfryCAD/gui/grid_info.py` - GridInfo precision support
2. `src/BelfryCAD/gui/views/graphics_items/control_points.py` - ControlDatum precision
3. `src/BelfryCAD/gui/views/widgets/cad_scene.py` - Scene precision management
4. `src/BelfryCAD/gui/views/graphics_items/caditems/circle_center_radius_cad_item.py` - CAD item precision
5. `src/BelfryCAD/gui/views/graphics_items/caditems/circle_2points_cad_item.py` - CAD item precision
6. `src/BelfryCAD/gui/views/graphics_items/caditems/circle_3points_cad_item.py` - CAD item precision
7. `src/BelfryCAD/gui/views/graphics_items/caditems/arc_cad_item.py` - CAD item precision
8. `src/BelfryCAD/gui/views/graphics_items/caditems/arc_corner_cad_item.py` - CAD item precision
9. `src/BelfryCAD/gui/views/graphics_items/caditems/circle_corner_cad_item.py` - CAD item precision
10. `src/BelfryCAD/gui/panes/config_pane.py` - ConfigPane precision
11. `src/BelfryCAD/gui/palette_system.py` - Palette system precision integration
12. `src/BelfryCAD/gui/main_window.py` - Main window precision integration

## Testing

Comprehensive test suites were created to verify precision functionality:

- `tests/test_precision_preferences.py` - Tests GridInfo, ControlDatum, ConfigPane, and scene precision
- `tests/test_control_datum_precision_updates.py` - Tests ControlDatum precision updates when shown and when preferences change

All tests pass successfully.

## Usage

Users can now change the decimal precision in the preferences dialog:

1. Open Preferences (File → Preferences)
2. Go to the "Units" tab
3. Adjust the "Decimal Precision" setting (0-10)
4. Click "Apply" or "OK"

The precision change will immediately affect:
- Grid labels and ruler displays
- Control datum labels on CAD items (both existing and newly shown)
- Float input fields in the properties panel

## ControlDatum Precision Updates

ControlDatums now update their precision in the following scenarios:

1. **When Precision Preference Changes**: All visible ControlDatums immediately update to reflect the new precision
2. **When ControlDatums Are Shown**: When a CAD item is selected and its controls are displayed, ControlDatums get the current scene precision
3. **When CAD Items Are Created**: New ControlDatums are created with the current scene precision

This ensures that ControlDatums always display with the correct precision, regardless of when they were created or shown.

## Backward Compatibility

The implementation maintains full backward compatibility:
- Default precision of 3 is used when not specified
- All existing code continues to work without modification
- Graceful fallbacks are in place for missing precision values

## Future Enhancements

Potential improvements for the future:
1. Unit-specific precision settings (different precision for inches vs mm)
2. Context-sensitive precision (different precision for different CAD operations)
3. Precision persistence per document
4. Visual feedback when precision changes are applied 