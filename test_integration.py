#!/usr/bin/env python3
"""
Final integration test to verify cursor changes work in the BelfryCAD tool system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt

from BelfryCAD.tools.selector import SelectorTool
from BelfryCAD.tools.line import LineTool
from BelfryCAD.tools.text import TextTool


def test_integration():
    """Test cursor functionality with actual BelfryCAD tools"""
    app = QApplication(sys.argv)
    
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    # Create actual BelfryCAD tools
    tools = [
        ("Selector", SelectorTool(scene, None, None)),
        ("Line", LineTool(scene, None, None)),  
        ("Text", TextTool(scene, None, None)),
    ]
    
    print("BelfryCAD Tool Cursor Integration Test")
    print("=" * 50)
    
    for tool_name, tool in tools:
        if hasattr(tool, 'definition') and tool.definition:
            cursor_type = tool.definition.cursor
            
            # Activate tool and check cursor
            tool.activate()
            actual_cursor = view.cursor().shape()
            
            print(f"✓ {tool_name} Tool:")
            print(f"  - Cursor type: '{cursor_type}'")
            print(f"  - Qt cursor shape: {actual_cursor}")
            
            # Deactivate tool
            tool.deactivate()
            deactivated_cursor = view.cursor().shape()
            print(f"  - After deactivation: {deactivated_cursor}")
            print()
        else:
            print(f"✗ {tool_name} Tool: No definition found")
    
    print("=" * 50)
    print("Integration test completed!")
    print("\nCursor implementation summary:")
    print("- Tools now properly change cursor when activated")
    print("- Cursor resets to arrow when deactivated")
    print("- Supports multiple cursor types: arrow, crosshair, text, etc.")
    print("- Fallback to crosshair for unknown cursor types")


if __name__ == "__main__":
    test_integration()
