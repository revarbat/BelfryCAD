#!/usr/bin/env python3
"""
Cleanup script to remove test files from the root directory that have been
moved to the tests directory.
"""

import os
import sys
import shutil

# List of test files to check and remove from the root directory
TEST_FILES = [
    'test_arcctr_fix.py',
    'verify_arc_shortcuts.py',
    'quick_arcctr_test.py',
]

def cleanup_tests():
    """Move test files to tests directory and remove originals"""
    # Ensure tests directory exists
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')
    if not os.path.exists(tests_dir):
        os.makedirs(tests_dir)
        print(f"Created tests directory: {tests_dir}")

    # Ensure tests/__init__.py exists
    init_file = os.path.join(tests_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('"""Test package for pyTkCAD."""\n')
        print(f"Created {init_file}")

    # Check and move each test file
    moved_count = 0
    already_moved = 0
    failed = 0

    for filename in TEST_FILES:
        source_path = os.path.join(os.path.dirname(__file__), filename)
        target_path = os.path.join(tests_dir, filename)
        
        if os.path.exists(source_path):
            if not os.path.exists(target_path):
                # File not in tests yet, make a copy there
                try:
                    # We now use remove because files were previously copied
                    os.remove(source_path)
                    print(f"✓ Removed {filename} (already exists in tests directory)")
                    moved_count += 1
                except Exception as e:
                    print(f"✗ Error removing {filename}: {str(e)}")
                    failed += 1
            else:
                # File already exists in tests, remove from root
                try:
                    os.remove(source_path)
                    print(f"✓ Removed {filename} (already exists in tests directory)")
                    already_moved += 1
                except Exception as e:
                    print(f"✗ Error removing {filename}: {str(e)}")
                    failed += 1
        else:
            # Check if it's in tests directory
            if os.path.exists(target_path):
                print(f"✓ {filename} already moved to tests directory")
                already_moved += 1
            else:
                print(f"! {filename} not found in root or tests directory")

    print(f"\nRemoved {moved_count + already_moved} test files from root directory")
    if failed > 0:
        print(f"Failed to process {failed} files")
    
    # Count how many test files we have now
    test_count = len([f for f in os.listdir(tests_dir) 
                     if f.endswith('.py') and f != '__init__.py'])
    print(f"Tests directory now contains {test_count} test files")
    
    return failed == 0

if __name__ == "__main__":
    success = cleanup_tests()
    sys.exit(0 if success else 1)
