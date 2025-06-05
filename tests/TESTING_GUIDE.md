# pyTkCAD Testing Guide

This guide explains how to run existing tests and create new tests for the pyTkCAD project.

## Running Tests

### Running Individual Tests

Use the Python module notation to run tests from the tests directory:

```bash
# From the project root directory
python -m tests.test_arcctr_fix

# For tests with GUI components
python -m tests.test_visual_tool_palette
```

### Running All Tests

You can run all tests using a script or pytest:

```bash
# Using pytest (if installed)
pytest tests/

# Or run a specific category of tests
pytest tests/test_*_shortcuts.py
```

## Creating New Tests

All new tests should be created in the tests directory. Follow these guidelines:

### 1. Use Proper Naming Conventions

- `test_*.py`: Standard test files
- `debug_*.py`: Debugging scripts
- `verify_*.py`: Verification scripts
- `validate_*.py`: Validation scripts
- `visual_test_*.py`: Tests that require visual inspection

### 2. Use the Test Template

Copy the template below for new tests:

```python
#!/usr/bin/env python3
"""
Test description goes here.
"""

import sys
import os
# Adjust import path to work from the tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary modules
from src.module import Class

def test_function():
    """Test specific functionality."""
    # Test code here
    assert True  # Add appropriate assertions

if __name__ == "__main__":
    test_function()
    print("All tests passed!")
```

### 3. Import Path Setup

Always use the correct import path setup to ensure tests can find the src directory:

```python
import sys
import os
# Adjust import path to work from the tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

### 4. Test Organization

- **Unit Tests**: Test individual components (one class/function)
- **Integration Tests**: Test interactions between components
- **GUI Tests**: Test user interface components
- **Validation Tests**: Simple scripts to verify functionality
- **Debug Tests**: Scripts for debugging specific issues

## Best Practices

1. **Include Description**: Each test file should have a docstring explaining what it tests
2. **Small and Focused**: Each test should focus on testing one thing well
3. **Descriptive Names**: Test functions should have descriptive names (e.g., test_arc_key_works_with_uppercase)
4. **Clean Up**: Tests should clean up after themselves (close windows, reset state)
5. **Document Special Requirements**: If a test needs special setup, document it at the top

## Examples

### Simple Unit Test

```python
def test_arc_tool_shortcut():
    """Test that the Arc tool uses the 'A' shortcut."""
    from src.tools.arcs import ArcCenterTool
    
    tool = ArcCenterTool(None, None, None)
    definition = tool.definitions[0]
    
    assert definition.secondary_key == 'C'
```

### GUI Test Example

```python
def test_tool_palette_shows_correctly():
    """Test that the tool palette shows correctly."""
    app = QApplication(sys.argv)
    
    # Create palette
    palette = ToolPalette(ToolCategory.ARCS, arc_tool_definitions, dummy_icon_loader)
    
    # Test specific properties
    assert palette.isVisible() == False
    
    # Show palette
    palette.show()
    assert palette.isVisible() == True
    
    # Clean up
    palette.hide()
    app.quit()
```
