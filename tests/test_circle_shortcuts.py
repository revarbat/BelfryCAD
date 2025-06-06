#!/usr/bin/env python3
"""
Test the updated Circle tool shortcuts in Ellipses category.
Verifies that CIRCLE2PT uses '2' and CIRCLE3PT uses '3'.
"""

def test_circle_shortcuts_in_file():
    """Test Circle shortcuts by reading the actual file content."""
    print("Verifying Circle tool shortcuts in tool_palette.py...")

    try:
        with open('src/gui/tool_palette.py', 'r') as f:
            content = f.read()

        # Check for the expected Circle tool mappings
        ellipses_section_found = False
        circle2pt_correct = False
        circle3pt_correct = False

        lines = content.split('\n')
        in_ellipses_section = False

        for line in lines:
            # Look for Ellipses category section
            if "ToolCategory.ELLIPSES:" in line:
                in_ellipses_section = True
                ellipses_section_found = True
                continue

            # Exit Ellipses section when we hit another category
            if in_ellipses_section and "ToolCategory." in line and "ELLIPSES" not in line:
                in_ellipses_section = False
                continue

            # Check for our specific mappings within Ellipses section
            if in_ellipses_section:
                if "'CIRCLE2PT': '2'" in line:
                    circle2pt_correct = True
                    print("✓ Found CIRCLE2PT: '2' (correct)")
                elif "'CIRCLE3PT': '3'" in line:
                    circle3pt_correct = True
                    print("✓ Found CIRCLE3PT: '3' (correct)")

        # Summary
        if ellipses_section_found:
            print("✓ Ellipses section found in file")
        else:
            print("✗ Ellipses section not found in file")

        success = ellipses_section_found and circle2pt_correct and circle3pt_correct

        if success:
            print("\n✓ All Circle tool shortcuts are correctly configured!")
            print("  - CIRCLE2PT uses '2' for 2 Points")
            print("  - CIRCLE3PT uses '3' for 3 Points")
        else:
            print("\n✗ Circle tool shortcuts verification failed:")
            if not circle2pt_correct:
                print("  - CIRCLE2PT: '2' not found")
            if not circle3pt_correct:
                print("  - CIRCLE3PT: '3' not found")

        return success

    except FileNotFoundError:
        print("✗ Could not find tool_palette.py file")
        return False
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False


if __name__ == "__main__":
    import sys
    import os

    # Change to the correct directory
    os.chdir('/Users/gminette/dev/git-repos/pyTkCAD')

    success = test_circle_shortcuts_in_file()
    sys.exit(0 if success else 1)
