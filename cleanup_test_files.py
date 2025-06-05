import os

# List of test files to check and remove from the root directory
test_files = [
    'test_arcctr_fix.py',
    'test_arcctr_secondary_key.py',
    'test_complete_keyboard_shortcuts.py',
    'test_conic_tools_arcs.py',
    'test_keyboard_shortcuts.py',
    'test_qt_preferences.py',
    'validate_keyboard_shortcuts.py',
    'debug_arcctr_key.py',
    'debug_grid.py',
    'visual_test_keyboard_shortcuts.py'
]

print("Checking for test files in root directory:")
removed_files = []
for filename in test_files:
    if os.path.exists(filename):
        # Check if the file exists in the tests directory
        if os.path.exists(os.path.join('tests', filename)):
            # Remove the file from root directory
            os.remove(filename)
            removed_files.append(filename)
            print(f"  Removed {filename} (already exists in tests directory)")
        else:
            print(f"  Warning: {filename} not found in tests directory, keeping in root")
    else:
        print(f"  {filename} not found in root directory")

print(f"\nRemoved {len(removed_files)} test files from root directory")
print("All test files should now be properly located in the tests directory")

# Verify tests directory structure
if os.path.exists('tests'):
    test_files_count = len([f for f in os.listdir('tests') 
                          if f.endswith('.py') and f != '__init__.py'])
    print(f"\nTests directory contains {test_files_count} test files")
else:
    print("\nWarning: tests directory does not exist!")