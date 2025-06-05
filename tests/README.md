# pyTkCAD Tests

This directory contains all tests for the pyTkCAD application.

## Test Organization

- **Unit Tests**: Test individual components (e.g., `test_cad_objects.py`)
- **Integration Tests**: Test interactions between components (e.g., `test_keyboard_shortcuts.py`)
- **Visual Tests**: Test GUI functionality (e.g., `test_tool_palette.py`)
- **Validation Tests**: Simple scripts to verify functionality (e.g., `validate_keyboard_shortcuts.py`)
- **Debug Tests**: Scripts for debugging specific issues (e.g., `debug_grid.py`)

## Running Tests

### Running a single test

```bash
# From project root
python -m tests.test_name
```

### Running all tests

```bash
# From project root
python -m unittest discover -s tests
```

## Creating New Tests

1. Use `test_template.py` as a starting point
2. Name tests descriptively based on what they test
3. Follow the unittest framework for structured tests
4. Include docstrings explaining what the test verifies
5. Clean up any resources used during testing

## Guidelines

- Keep tests independent of each other
- Avoid tests that depend on specific environment conditions
- Write both positive and negative test cases
- Verify edge cases and error handling
- Run tests frequently to catch regressions early