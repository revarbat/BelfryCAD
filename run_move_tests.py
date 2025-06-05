#!/usr/bin/env python3
"""
Run this script to execute the move_tests.py script
and verify the results.
"""

import subprocess
import sys
import os

print("Moving all test files to tests directory...")
result = subprocess.run([sys.executable, 'move_all_tests.py'], 
                        capture_output=True, text=True)

# Print the output
print(result.stdout)

# Check for errors
if result.returncode != 0:
    print("Error:", result.stderr)
else:
    print("Script completed successfully!")

# Count test files in tests directory
test_count = 0
if os.path.exists('tests'):
    for filename in os.listdir('tests'):
        if filename.endswith('.py') and not filename == '__init__.py':
            test_count += 1
    print(f"Tests directory now contains {test_count} test files.")

print("\nNote: Update any imports or run commands in your documentation to reference")
print("tests in their new location, e.g., 'python -m tests.test_name' instead of")
print("'python test_name.py'.")