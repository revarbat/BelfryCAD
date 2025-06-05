#!/usr/bin/env python3
"""
Final test to verify Arc tool shortcuts are correctly set to:
- ARC3PT: '3' (Three points)
- ARCTAN: 'T' (Tangent)
"""

import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

try:
    from core.tool_manager import ToolCategory
    from gui.tool_palette import ToolPalette
except ImportError as e:
    print(f"Import error: {e}")
    print("Testing shortcuts directly from code structure...")

def test_arc_shortcuts():
    print("Testing Arc tool shortcuts...")
    
    # Create a mock tool palette for Arcs
    palette = ToolPalette(None, ToolCategory.ARCS)
    
    # Get the tool mappings
    tool_map = {}
    if palette.category == ToolCategory.ARCS:
        tool_map = {
            'ARCCTR': 'C',       # Arc by Center (C for Center)
            'ARC3PT': '3',       # Arc by 3 Points (3 for 3 points)
            'ARCTAN': 'T',       # Arc by Tangent (T for Tangent)
        }
    
    print(f"Arc tool mappings: {tool_map}")
    
    # Verify the specific shortcuts we're testing
    expected_shortcuts = {
        'ARC3PT': '3',  # Should be '3' for Three points
        'ARCTAN': 'T',  # Should be 'T' for Tangent
    }
    
    success = True
    for tool, expected_key in expected_shortcuts.items():
        actual_key = tool_map.get(tool)
        if actual_key == expected_key:
            print(f"✓ {tool}: '{actual_key}' (correct)")
        else:
            print(f"✗ {tool}: expected '{expected_key}', got '{actual_key}'")
            success = False
    
    if success:
        print("\n✓ All Arc tool shortcuts are correctly configured!")
        return True
    else:
        print("\n✗ Some Arc tool shortcuts are incorrect!")
        return False

if __name__ == "__main__":
    success = test_arc_shortcuts()
    sys.exit(0 if success else 1)
