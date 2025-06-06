# Test Organization

## Overview

All test files in the pyTkCAD project have been organized into the `tests`
directory. This improves project structure and makes test management easier.

## Changes Made

1. **Relocated test files:**
   - Moved all test_*.py files to the tests directory
   - Moved all debug_*.py files to the tests directory
   - Moved all validate_*.py files to the tests directory
   - Moved all visual_test_*.py files to the tests directory

2. **Updated import paths:**
   - Modified sys.path in test files to work from tests directory
   - Tests now use: `sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))`

3. **Created tests package:**
   - Added `__init__.py` to the tests directory
   - Tests can now be run as modules

## Running Tests

Tests should now be run as modules from the project root:

```bash
# Old way (no longer works)
python test_name.py

# New way
python -m tests.test_name
```

## Example

For example, to run the ARCCTR secondary key fix test:

```bash
# From project root
python -m tests.test_arcctr_fix
```

## Benefits

- Cleaner project root directory
- Better organization of test files
- Easier test discovery
- Follows Python package conventions
- Simplified test management