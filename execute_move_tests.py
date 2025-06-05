import os
import sys
import subprocess

# Get the current directory
current_dir = os.getcwd()

# Execute the move_tests.py script
print("Moving test files to tests directory...")
result = subprocess.run([sys.executable, os.path.join(current_dir, "move_tests.py")], 
                        capture_output=True, text=True)

# Print the output
print(result.stdout)

# Check for errors
if result.returncode != 0:
    print("Error:", result.stderr)

print("\nTest organization complete!")
print("All test files have been moved to the tests directory.")
print("Remember to run tests using 'python -m tests.test_name'.")