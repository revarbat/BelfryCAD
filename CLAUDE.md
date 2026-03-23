# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

BelfryCAD is a 2.5D CAD/CAM application built with Python and PySide6, ported from the original TkCAD TCL/Tk implementation. The TCL reference code is in `tksrc/lib/` for historical reference.

## Commands

```bash
# Setup virtual environment
./dev.sh setup

# Run the application (activates venv automatically)
./dev.sh run
# or
source venv/bin/activate && python main.py

# Run all tests
source venv/bin/activate && python -m pytest tests/

# Run a single test file
source venv/bin/activate && python -m pytest tests/test_cad_viewmodel.py

# Build distribution package
python -m build
```

**Important:** Always activate the venv before running scripts. The venv is in `venv/`.

## Architecture: MVVM Pattern

The codebase follows strict MVVM separation. Each layer has hard rules about dependencies:

### Model (`src/BelfryCAD/models/`)
- Pure business logic — **no Qt or UI dependencies**
- `CadObject` base class; subclasses live in `models/cad_objects/`
- `Document` manages collections of `CadObject` instances
- `ConstraintsManager` handles geometric constraint solving
- `UndoRedoManager` for undo/redo

### ViewModel (`src/BelfryCAD/gui/viewmodels/`)
- Bridges Model and View using PySide6 signals
- `CadViewModel` base class; subclasses in `gui/viewmodels/cad_viewmodels/`
- Manages control points and control datums (interactive handles shown when one object is selected)
- Each ViewModel exposes `createControls()`, `updateControls()`, `showControls()`, `hideControls()`

### View (`src/BelfryCAD/gui/`)
- All Qt graphics rendering; no business logic
- `CadScene` — the main `QGraphicsScene`
- `CadItem` base for `QGraphicsItem` subclasses → lives in `gui/graphics_items/caditems/`
- `DocumentWindow` — main application window
- Dialogs → `gui/dialogs/`; Docked panels/palettes → `gui/panes/`

### Geometry (`src/BelfryCAD/cad_geometry/`)
- Pure geometry classes (Point2D, Arc, Circle, Bezier, etc.) with **no Qt or model dependencies**
- Used by both Model and ViewModel layers

### Tools (`src/BelfryCAD/tools/`)
- User interaction handlers that implement drawing operations
- Inherit from `Tool` base class (`tools/base.py`)

### CNC/CAM (`src/BelfryCAD/mlcnc/`)
- G-code generation, tool paths, feed rate optimization, material database

## File Placement Rules

| What | Where |
|------|-------|
| GUI dialogs | `gui/dialogs/` |
| `QGraphicsItem` subclasses | `gui/graphics_items/` |
| `CadItem` subclasses | `gui/graphics_items/caditems/` |
| Docked panels / palettes | `gui/panes/` |
| `Tool` subclasses | `tools/` |
| G-code generation | `mlcnc/` |
| Tests | `tests/` |
| Architecture/design docs | `dev_docs/` |
| Icons (SVG only) | `resources/icons/` |

## Naming Conventions

- Classes: `PascalCase` (e.g., `CadItem`, `SnapsSystem`)
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Control Points and Datums

When exactly one `CadItem` is selected, its ControlPoints (draggable position handles) and ControlDatums (editable numeric values) are shown. They scale with the view so they always appear the same visual size regardless of zoom. `pos_setter` and `data_setter` callbacks have recursive-call guards. See `dev_docs/SELECTION_AND_CONTROLS.md` for the full spec.

## Selection Behavior

- Click: select single item
- Shift+click: add to selection (no-op if already selected)
- Cmd+click: toggle selection

ControlPoints/Datums are only shown when exactly one item is selected.

## Document File Format

Files use the `.belcadx` extension (XML format). See `dev_docs/XML_FILE_FORMAT_SPECIFICATION.md` and `dev_docs/BELCADX_FORMAT_IMPLEMENTATION.md` for the schema.
