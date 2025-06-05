#!/usr/bin/env python3
"""
Simple test to verify letter-based secondary shortcuts work correctly.
"""

import os
import sys

# Add the project root directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from src.config import AppConfig
from src.core.document import Document
from src.core.preferences import PreferencesManager
from src.gui.main_window import MainWindow
from src.gui.tool_palette import ToolPalette
from src.tools.base import ToolCategory, ToolDefinition


def test_letter_shortcuts():
    """Test that letter-based secondary shortcuts work"""
    print("Testing Letter-Based Secondary Shortcuts")
    print("=======================================")
    
    # Create a simple test with Node tools
    tools = [
        ToolDefinition(
            token='NODESEL',
            name='Select Nodes', 
            category=ToolCategory.NODES,
            icon='tool-nodesel'
        ),
        ToolDefinition(
            token='NODEADD',
            name='Add Node',
            category=ToolCategory.NODES, 
            icon='tool-nodeadd'
        ),
        ToolDefinition(
            token='NODEDEL',
            name='Delete Node',
            category=ToolCategory.NODES,
            icon='tool-nodedel'
        ),
    ]
    
    def dummy_icon_loader(icon_name):
        return None
    
    # Create tool palette
    palette = ToolPalette(ToolCategory.NODES, tools, dummy_icon_loader)
    
    # Test expected letter mappings
    expected_mappings = {
        'S': 'NODESEL',
        'A': 'NODEADD', 
        'D': 'NODEDEL',
    }
    
    print("Testing Node tools secondary shortcuts:")
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
    print("✓ Letter-based secondary shortcuts working correctly!")
    return True


def main():
    app = QApplication([])
    
    try:
        success = test_letter_shortcuts()
        if success:
            print("\n🎉 ALL LETTER SHORTCUT TESTS PASSED!")
            return 0
        else:
            print("\n❌ Letter shortcut tests failed")
            return 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1
    finally:
        app.quit()


if __name__ == "__main__":
    sys.exit(main())
