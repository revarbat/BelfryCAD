#!/usr/bin/env python3
"""
This script executes the test file relocation process.
Run this to move test files to the tests directory and clean up.
"""

import os
import shutil
import re

# Step 1: Create tests directory if it doesn't exist
if not os.path.exists('tests'):
    os.makedirs('tests')
    print("Created tests directory")

# Step 2: Ensure tests directory has __init__.py
init_file = os.path.join('tests', '__init__.py')
if not os.path.exists(init_file):
    with open(init_file, 'w') as f:
        f.write('"""Test package for pyTkCAD."""\n')
    print("Created tests/__init__.py")

# Step 3: Copy test files to tests directory
test_patterns = ['test_', 'debug_', 'validate_', 'visual_test_']
moved_files = []

for filename in os.listdir('.'):
    if (any(filename.startswith(pattern) for pattern in test_patterns) and 
            filename.endswith('.py') and os.path.isfile(filename)):
        src = filename
        dst = os.path.join('tests', filename)
        
        if os.path.exists(dst):
            print(f"File already exists: {dst}")
        else:
            shutil.copy2(src, dst)
            moved_files.append(filename)
            print(f"Copied {src} to {dst}")

# Step 4: Verify files were copied correctly
verify_success = True
for filename in moved_files:
    if not os.path.exists(os.path.join('tests', filename)):
        print(f"Error: Failed to copy {filename}")
        verify_success = False

# Step 5: If all files were copied successfully, remove originals
if verify_success and moved_files:
    print("\nRemoving original files from root directory...")
    for filename in moved_files:
        os.remove(filename)
        print(f"Removed {filename}")
    print(f"Successfully moved {len(moved_files)} test files to tests directory")
elif not moved_files:
    print("No test files found in root directory")

# Step 6: Final verification
print("\nFinal verification:")
test_files_root = []
for filename in os.listdir('.'):
    if (any(filename.startswith(pattern) for pattern in test_patterns) and 
            filename.endswith('.py') and os.path.isfile(filename)):
        test_files_root.append(filename)

if test_files_root:
    print(f"Warning: {len(test_files_root)} test files still in root directory:")
    for filename in test_files_root:
        print(f"  - {filename}")
else:
    print("✅ No test files remaining in root directory")

test_files_tests = []
if os.path.exists('tests'):
    for filename in os.listdir('tests'):
        if (any(filename.startswith(pattern) for pattern in test_patterns) and 
                filename.endswith('.py') and os.path.isfile(os.path.join('tests', filename))):
            test_files_tests.append(filename)
    print(f"✅ {len(test_files_tests)} test files in tests directory")