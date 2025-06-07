#!/usr/bin/env python3
"""
Test script to verify cursor changes are working correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from BelfryCAD.tools.selector import SelectorTool
from BelfryCAD.tools.line import LineTool


def test_cursor_functionality():
    """Test that cursor changes work correctly"""
    app = QApplication(sys.argv)
    
    # Create a simple scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    # Create tools
    selector_tool = SelectorTool(scene, None, None)
    line_tool = LineTool(scene, None, None)
    
    print("Testing cursor functionality...")
    
    # Test selector tool
    print(f"Selector tool cursor: {selector_tool.definition.cursor}")
    selector_tool.activate()
    cursor = view.cursor()
    print(f"View cursor after selector activation: {cursor.shape()}")
    print(f"Expected: {Qt.CursorShape.ArrowCursor} (ArrowCursor)")
    
    # Test line tool
    print(f"\nLine tool cursor: {line_tool.definition.cursor}")
    line_tool.activate()
    cursor = view.cursor()
    print(f"View cursor after line activation: {cursor.shape()}")
    print(f"Expected: {Qt.CursorShape.CrossCursor} (CrossCursor)")
    
    # Test deactivation
    line_tool.deactivate()
    cursor = view.cursor()
    print(f"\nView cursor after line deactivation: {cursor.shape()}")
    print(f"Expected: {Qt.CursorShape.ArrowCursor} (ArrowCursor)")
    
    print("\nCursor test completed!")
    

if __name__ == "__main__":
    test_cursor_functionality()
