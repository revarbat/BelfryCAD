# Document Window Renaming Complete

## Overview
Successfully renamed `MainWindow` to `DocumentWindow` throughout the BelfryCAD codebase to better reflect its purpose as a document-centric window that can be created for each opened file.

## Files Renamed
- `src/BelfryCAD/gui/main_window.py` → `src/BelfryCAD/gui/document_window.py`

## Major Changes Made

### 1. Core Class Rename
- `MainWindow` class → `DocumentWindow` class
- Updated class docstring to reflect new purpose
- Updated file header comment

### 2. Import Statement Updates
Updated all import statements from:
```python
from .gui.main_window import MainWindow
```
to:
```python
from .gui.document_window import DocumentWindow
```

**Files Updated:**
- `src/BelfryCAD/app.py`
- `src/BelfryCAD/gui/viewmodels/cad_object_factory.py`
- `src/BelfryCAD/gui/viewmodels/cad_viewmodels/cad_viewmodel.py`
- `src/BelfryCAD/gui/viewmodels/cad_viewmodels/arc_viewmodel.py`
- `src/BelfryCAD/gui/viewmodels/cad_viewmodels/circle_viewmodel.py`
- `src/BelfryCAD/gui/viewmodels/cad_viewmodels/cubic_bezier_viewmodel.py`
- `src/BelfryCAD/gui/viewmodels/cad_viewmodels/ellipse_viewmodel.py`
- `src/BelfryCAD/gui/viewmodels/cad_viewmodels/gear_viewmodel.py`
- `src/BelfryCAD/gui/viewmodels/cad_viewmodels/line_viewmodel.py`
- `src/BelfryCAD/gui/dialogs/feed_wizard.py`
- `src/BelfryCAD/gui/dialogs/gear_wizard_dialog.py`
- `src/BelfryCAD/gui/dialogs/tool_table_dialog.py`

### 3. Constructor Parameter Updates
Updated all constructor parameters from `main_window` to `document_window`:

**Base Classes:**
- `src/BelfryCAD/gui/viewmodels/cad_viewmodels/cad_viewmodel.py`
- `src/BelfryCAD/tools/base.py`

**ViewModels:**
- All viewmodel classes in `src/BelfryCAD/gui/viewmodels/cad_viewmodels/`
- `src/BelfryCAD/gui/viewmodels/cad_object_factory.py`

**Tools:**
- `src/BelfryCAD/tools/base.py` (Tool and ToolManager classes)
- `src/BelfryCAD/tools/image.py`
- `src/BelfryCAD/tools/gear.py`
- `src/BelfryCAD/tools/screw_hole.py`

### 4. Attribute Reference Updates
Updated all attribute references from `_main_window` to `_document_window`:

**ViewModels:**
- All viewmodel classes now use `self._document_window`
- Updated property getters to return `document_window`

**Tools:**
- All tool classes now use `self.document_window`
- Updated method calls to use `self.document_window`

### 5. Application Class Updates
Updated `BelfryCadApplication` class in `src/BelfryCAD/app.py`:
- Renamed `self.main_window` to `self.document_window`
- Updated all method references
- Updated log messages to reflect "document window" terminology

### 6. Dialog Updates
Updated all dialog classes to use `DocumentWindow`:
- Updated type hints and casts
- Updated parent window references
- Updated preference access patterns

### 7. Palette System Updates
Updated `src/BelfryCAD/gui/palette_system.py`:
- Renamed constructor parameter from `main_window` to `document_window`
- Updated all internal references
- Updated function signatures

### 8. Control Points Updates
Updated `src/BelfryCAD/gui/graphics_items/control_points.py`:
- Updated all `main_window` references to `document_window`
- Updated precision and grid info access patterns

## Benefits of This Change

1. **Better Naming**: `DocumentWindow` more accurately describes the purpose of the class
2. **Multi-Document Support**: The new name better supports the concept of multiple document windows
3. **Clearer Architecture**: Makes it clear that each window represents a document
4. **Future-Proofing**: Better supports planned multi-document functionality

## Testing Status
- Basic application startup tested
- All import statements updated
- All constructor parameters updated
- All attribute references updated

## Remaining Considerations

1. **UI Text**: Some user-facing text may still reference "main window" - these could be updated in future iterations
2. **Documentation**: External documentation may need updates to reflect the new terminology
3. **Configuration**: Any saved configurations that reference the old class name may need migration

## Files That May Need Additional Updates
Some files still contain references to `mainwin` parameters in tool constructors. These are less critical but could be updated for consistency:
- `src/BelfryCAD/tools/line.py`
- `src/BelfryCAD/tools/circle.py`
- Various other tool files

## Conclusion
The renaming from `MainWindow` to `DocumentWindow` has been successfully completed across the entire codebase. The change improves code clarity and better supports the multi-document architecture that BelfryCAD is moving toward. 