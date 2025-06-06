#!/usr/bin/env python3
"""
Test the updated Arc category shortcuts.
"""

import os
import sys

# Add the project root directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from BelfryCAD.gui.tool_palette import ToolPalette
from BelfryCAD.tools.base import ToolCategory, ToolDefinition


def test_arc_shortcuts():
    """Test that Arc category shortcuts work correctly"""
    print("Testing Arc Category Secondary Shortcuts")
    print("=======================================")
    
    # Create Arc tools
    tools = [
        ToolDefinition(
            token='ARCCTR',
            name='Arc by Center', 
            category=ToolCategory.ARCS,
            icon='tool-arcctr'
        ),
        ToolDefinition(
            token='ARC3PT',
            name='Arc by 3 Points',
            category=ToolCategory.ARCS, 
            icon='tool-arc3pt'
        ),
        ToolDefinition(
            token='ARCTAN',
            name='Arc by Tangent',
            category=ToolCategory.ARCS,
            icon='tool-arctan'
        ),
    ]
    
    def dummy_icon_loader(icon_name):
        return None
    
    # Create tool palette
    palette = ToolPalette(ToolCategory.ARCS, tools, dummy_icon_loader)
    
    # Test expected mappings
    expected_mappings = {
        'C': 'ARCCTR',
        '3': 'ARC3PT', 
        'T': 'ARCTAN',
    }
    
    print("Testing Arc tools secondary shortcuts:")
    for key, expected_token in expected_mappings.items():
        if key in palette.secondary_key_mappings:
            actual_token = palette.secondary_key_mappings[key]
            if actual_token == expected_token:
                print(f"  ✓ '{key}' -> {actual_token}")
            else:
                print(f"  ✗ '{key}' -> {actual_token}, expected {expected_token}")
                return False
        else:
            print(f"  ✗ Key '{key}' not found in mappings")
            return False
    
    print()
    print("✓ Arc category shortcuts working correctly!")
    return True


def main():
    app = QApplication([])
    
    try:
        success = test_arc_shortcuts()
        if success:
            print("\n🎉 ARC SHORTCUT TESTS PASSED!")
            return 0
        else:
            print("\n❌ Arc shortcut tests failed")
            return 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1
    finally:
        app.quit()


if __name__ == "__main__":
    sys.exit(main())
