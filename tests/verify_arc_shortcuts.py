#!/usr/bin/env python3
"""
Simple verification test for Arc tool shortcuts.
Tests that ARC3PT='3' and ARCTAN='T' in tool_palette.py
"""

import os
import sys
# Adjust import path to work from the tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_arc_shortcuts_in_file():
    """Test Arc shortcuts by reading the actual file content."""
    print("Verifying Arc tool shortcuts in tool_palette.py...")
    
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'gui', 'tool_palette.py')
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for the expected Arc tool mappings
        arc_section_found = False
        arc3pt_correct = False
        arctan_correct = False
        
        lines = content.split('\n')
        in_arc_section = False
        
        for line in lines:
            # Look for Arc category section
            if "ToolCategory.ARCS:" in line:
                in_arc_section = True
                arc_section_found = True
                continue
            
            # Exit Arc section when we hit another category
            if in_arc_section and "ToolCategory." in line and "ARCS" not in line:
                in_arc_section = False
                continue
            
            # Check for our specific mappings within Arc section
            if in_arc_section:
                if "'ARC3PT': '3'" in line:
                    arc3pt_correct = True
                    print("✓ Found ARC3PT: '3' (correct)")
                elif "'ARCTAN': 'T'" in line:
                    arctan_correct = True
                    print("✓ Found ARCTAN: 'T' (correct)")
        
        # Summary
        if arc_section_found:
            print("✓ Arc section found in file")
        else:
            print("✗ Arc section not found in file")
        
        success = arc_section_found and arc3pt_correct and arctan_correct
        
        if success:
            print("\n✓ All Arc tool shortcuts are correctly configured!")
            print("  - ARC3PT uses '3' for Three points")
            print("  - ARCTAN uses 'T' for Tangent")
        else:
            print("\n✗ Arc tool shortcuts verification failed:")
            if not arc3pt_correct:
                print("  - ARC3PT: '3' not found")
            if not arctan_correct:
                print("  - ARCTAN: 'T' not found")
        
        return success
        
    except FileNotFoundError:
        print("✗ Could not find tool_palette.py file")
        return False
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return False


if __name__ == "__main__":
    # Change to the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(project_root)
    
    success = test_arc_shortcuts_in_file()
    sys.exit(0 if success else 1)
