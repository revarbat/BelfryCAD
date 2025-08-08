# AI Development Guidelines

## Context
This is BelfryCAD, a CAD application built with Python and PySide6.

## Code Patterns
- Use PySide6.QtWidgets for GUI components
- Follow the existing class hierarchy (CadItem, CadScene, etc.)
- Implement proper signal/slot connections
- Use type hints for function parameters and return values

## File Organization
- Virtual Python Environment: `venv/` directory
- Core logic: `core/` directory
- GUI components: `gui/` directory
- Specialized GUI Widgets: `gui/widgets` directory
- Specialized QGraphicsItem derived items: `gui/graphics_items/` directory
- CadItem derived items: `gui/graphics_items/caditems/` directory
- QToolBar/QDockWidget derived GUI panes and palettes: `gui/panes/` directory
- GUI Dialogs: `gui/dialogs/` directory
- CNC and GCode generation: `mlcnc/` directory
- Tools: `tools/` directory  
- Utilities: `utils/` directory
- Tests: `tests/` directory
- Code Docs: `dev_docs/` directory

## Naming Conventions
- Classes: PascalCase (e.g., `CadItem`, `SnapsSystem`)
- Functions: snake_case (e.g., `get_control_points`)
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE

## Common Patterns
- Use `@property` decorators for getters/setters
- Implement `__init__.py` files for packages
- Follow Qt's parent-child widget relationships

## Virtual Environment
- It is very important that the venv virtual environment is always activated before running a script.