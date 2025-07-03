#!/usr/bin/env python3
"""
Test script for Command-click cycling in CubicBezierCadItem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor
from BelfryCAD.gui.caditems.cubic_bezier_cad_item import CubicBezierCadItem, PathPointState


def test_command_click_cycling():
    """Test Command-click cycling functionality."""
    print("Testing Command-click cycling...")
    
    # Create a simple cubic Bezier curve
    points = [
        QPointF(0, 0),    # Path point 0
        QPointF(1, 1),    # Control 1 for segment 0
        QPointF(2, -1),   # Control 2 for segment 0
        QPointF(3, 0),    # Path point 1
        QPointF(4, 1),    # Control 1 for segment 1
        QPointF(5, -1),   # Control 2 for segment 1
        QPointF(6, 0),    # Path point 2
    ]
    
    bezier = CubicBezierCadItem(points, QColor(0, 0, 255), 0.05)
    
    # Test cycling through states for path point 1 (index 3)
    print("\nTest 1: Cycling through states for path point 1")
    
    # Start with SMOOTH state
    bezier.set_path_point_state(1, PathPointState.SMOOTH)
    print(f"Initial state: {bezier.get_path_point_state(1)}")
    
    # Simulate Command-click on the path point control point
    # The control point index for path point 1 (index 3) is 3
    result = bezier._handle_control_point_click(3, Qt.KeyboardModifier.ControlModifier)
    print(f"Command-click result: {result}")
    print(f"State after Command-click: {bezier.get_path_point_state(1)}")
    
    # Cycle again
    result = bezier._handle_control_point_click(3, Qt.KeyboardModifier.ControlModifier)
    print(f"Second Command-click result: {result}")
    print(f"State after second Command-click: {bezier.get_path_point_state(1)}")
    
    # Cycle again
    result = bezier._handle_control_point_click(3, Qt.KeyboardModifier.ControlModifier)
    print(f"Third Command-click result: {result}")
    print(f"State after third Command-click: {bezier.get_path_point_state(1)}")
    
    # Test 2: Command-click on non-path point should not cycle
    print("\nTest 2: Command-click on control point (should not cycle)")
    result = bezier._handle_control_point_click(1, Qt.KeyboardModifier.ControlModifier)  # Control point
    print(f"Command-click on control point result: {result}")
    
    # Test 3: Click without Command modifier should not cycle
    print("\nTest 3: Click without Command modifier (should not cycle)")
    result = bezier._handle_control_point_click(3, Qt.KeyboardModifier.NoModifier)  # No modifier
    print(f"Click without Command result: {result}")
    
    print("All Command-click cycling tests completed!")


if __name__ == "__main__":
    test_command_click_cycling() 