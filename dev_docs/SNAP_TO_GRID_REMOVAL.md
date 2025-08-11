# Snap to Grid Removal from Document Preferences

## Overview

Removed `snap_to_grid` from document preferences as it is more appropriately a user interface preference rather than a document-specific setting.

## Rationale

- **UI vs Document Setting**: `snap_to_grid` is a user interface behavior that affects how the user interacts with the application, not a property of the document itself
- **Consistency**: Other UI preferences like `snap_to_grid` should be stored in application preferences, not document preferences
- **Separation of Concerns**: Document preferences should focus on display and measurement settings, while UI behavior should be application-wide

## Changes Made

### 1. **`src/BelfryCAD/utils/xml_serializer.py`**
- Removed `snap_to_grid` from the boolean preferences parsing in `_parse_document_header()`

### 2. **`examples/xml_serializer_example.py`**
- Removed `'snap_to_grid': True` from the preferences dictionary

### 3. **`tests/test_xml_serializer.py`**
- Removed `'snap_to_grid': True` from the test preferences dictionary

### 4. **`dev_docs/XML_FILE_FORMAT_SPECIFICATION.md`**
- Removed `snap_to_grid="true"` from both XML examples in the documentation

## Document Preferences After Change

The following preferences remain as document-specific settings:

- `units` - Measurement units (mm, cm, m, inches, ft, yd)
- `precision` - Decimal places for display
- `use_fractions` - Use fractions instead of decimals
- `grid_visible` - Show grid
- `show_rulers` - Show rulers
- `canvas_bg_color` - Canvas background color
- `grid_color` - Grid color
- `selection_color` - Selection highlight color

## Application Preferences

`snap_to_grid` should be stored in application preferences (not document preferences) along with other UI behavior settings like:
- Tool preferences
- Keyboard shortcuts
- Mouse behavior
- View settings

## Testing

- All 9 tests pass ✅
- Example script works correctly ✅
- No regressions in functionality ✅

## Impact

This change improves the separation between document-specific settings and application-wide UI preferences, making the system more maintainable and logically organized. 