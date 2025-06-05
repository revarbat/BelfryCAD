#!/usr/bin/env python3
"""
Test the updated ELLIPSECTR tool shortcut.
Verifies that ELLIPSECTR uses 'E'.
"""

def test_ellipsectr_shortcut_in_file():
    """Test ELLIPSECTR shortcut by reading the actual file content."""
    print("Verifying ELLIPSECTR tool shortcut in tool_palette.py...")
    
    try:
        with open('src/gui/tool_palette.py', 'r') as f:
            content = f.read()
        
        # Check for the expected ELLIPSECTR tool mapping
        ellipses_section_found = False
        ellipsectr_correct = False
        
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
            
            # Check for our specific mapping within Ellipses section
            if in_ellipses_section:
                if "'ELLIPSECTR': 'E'" in line:
                    ellipsectr_correct = True
                    print("✓ Found ELLIPSECTR: 'E' (correct)")
        
        # Summary
        if ellipses_section_found:
            print("✓ Ellipses section found in file")
        else:
            print("✗ Ellipses section not found in file")
        
        success = ellipses_section_found and ellipsectr_correct
        
        if success:
            print("\n✓ ELLIPSECTR tool shortcut is correctly configured!")
            print("  - ELLIPSECTR uses 'E' for Ellipse")
        else:
            print("\n✗ ELLIPSECTR tool shortcut verification failed:")
            if not ellipsectr_correct:
                print("  - ELLIPSECTR: 'E' not found")
        
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
    
    success = test_ellipsectr_shortcut_in_file()
    sys.exit(0 if success else 1)
