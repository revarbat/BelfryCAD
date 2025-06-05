#!/usr/bin/env python3
"""
Script to move all test_*.py files from the root directory to the tests directory
"""

import os
import shutil

# Ensure tests directory exists
if not os.path.exists('tests'):
    os.makedirs('tests')
    print("Created tests directory")

# Ensure tests directory has __init__.py
init_file = os.path.join('tests', '__init__.py')
if not os.path.exists(init_file):
    with open(init_file, 'w') as f:
        f.write('"""Test package for pyTkCAD."""\n')
    print("Created tests/__init__.py")

# Find all test_*.py files in the root directory
test_files = []
for filename in os.listdir('.'):
    if (filename.startswith('test_') or 
        filename.startswith('debug_') or
        filename.startswith('validate_') or
        filename.startswith('visual_test_')) and filename.endswith('.py'):
        if os.path.isfile(filename):
            test_files.append(filename)

# Move each test file to the tests directory
if test_files:
    print(f"Moving {len(test_files)} test files to tests directory:")
    for filename in test_files:
        src = filename
        dst = os.path.join('tests', filename)
        
        if os.path.exists(dst):
            print(f"  - {filename} (skipped - already exists in tests directory)")
        else:
            shutil.move(src, dst)
            print(f"  - {filename} (moved)")
    print("All test files have been moved to the tests directory")
else:
    print("No test files found in the root directory")