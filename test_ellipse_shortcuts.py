#!/usr/bin/env python3
"""
Test the updated Ellipse tool shortcuts.
Verifies that ELLIPSE3COR uses 'O' and ELLIPSECTAN uses 'T'.
"""

def test_ellipse_shortcuts_in_file():
    """Test Ellipse shortcuts by reading the actual file content."""
    print("Verifying Ellipse tool shortcuts in tool_palette.py...")
    
    try:
        with open('src/gui/tool_palette.py', 'r') as f:
            content = f.read()
        
        # Check for the expected Ellipse tool mappings
        ellipses_section_found = False
        ellipse3cor_correct = False
        ellipsectan_correct = False
        
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
                if "'ELLIPSE3COR': 'O'" in line:
                    ellipse3cor_correct = True
                    print("✓ Found ELLIPSE3COR: 'O' (correct)")
                elif "'ELLIPSECTAN': 'T'" in line:
                    ellipsectan_correct = True
                    print("✓ Found ELLIPSECTAN: 'T' (correct)")
        
        # Summary
        if ellipses_section_found:
            print("✓ Ellipses section found in file")
        else:
            print("✗ Ellipses section not found in file")
        
        success = ellipses_section_found and ellipse3cor_correct and ellipsectan_correct
        
        if success:
            print("\n✓ All Ellipse tool shortcuts are correctly configured!")
            print("  - ELLIPSE3COR uses 'O' for cOrner")
            print("  - ELLIPSECTAN uses 'T' for Tangent")
        else:
            print("\n✗ Ellipse tool shortcuts verification failed:")
            if not ellipse3cor_correct:
                print("  - ELLIPSE3COR: 'O' not found")
            if not ellipsectan_correct:
                print("  - ELLIPSECTAN: 'T' not found")
        
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
    
    success = test_ellipse_shortcuts_in_file()
    sys.exit(0 if success else 1)
