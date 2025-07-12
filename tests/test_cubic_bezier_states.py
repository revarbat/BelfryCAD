#!/usr/bin/env python3
"""
Test script for CubicBezierCadItem state cycling
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from ..src.BelfryCAD.gui.views.graphics_items.caditems.cubic_bezier_cad_item import CubicBezierCadItem, PathPointState

def test_cubic_bezier_states():
    """Test the CubicBezierCadItem state cycling implementation."""
    print("Testing CubicBezierCadItem state cycling...")
    
    # Test basic instantiation
    points = [
        QPointF(0, 0),    # 1st path point (SMOOTH by default)
        QPointF(1, 1),    # control1 for 1st segment
        QPointF(2, -1),   # control2 for 1st segment
        QPointF(3, 0),    # 2nd path point (SMOOTH by default)
        QPointF(4, 1),    # control1 for 2nd segment
        QPointF(5, -1),   # control2 for 2nd segment
    ]
    
    bezier = CubicBezierCadItem(points, QColor(0, 0, 255), 0.1)
    
    # Test initial states
    print(f"Initial path point states: {bezier.get_all_path_point_states()}")
    print(f"Path point 0 state: {bezier.get_path_point_state(0)}")
    print(f"Path point 1 state: {bezier.get_path_point_state(1)}")
    
    # Test state cycling
    print("\nTesting state cycling...")
    
    # Import the enum
    # from ..BelfryCAD.gui.caditems.cubic_bezier_cad_item import PathPointState
    
    # Cycle first path point to EQUIDISTANT
    bezier.set_path_point_state(0, PathPointState.EQUIDISTANT)
    print(f"After setting to EQUIDISTANT: {bezier.get_path_point_state(0)}")
    
    # Cycle first path point to DISJOINT
    bezier.set_path_point_state(0, PathPointState.DISJOINT)
    print(f"After setting to DISJOINT: {bezier.get_path_point_state(0)}")
    
    # Cycle first path point back to SMOOTH
    bezier.set_path_point_state(0, PathPointState.SMOOTH)
    print(f"After setting to SMOOTH: {bezier.get_path_point_state(0)}")
    
    # Test constraint application
    print("\nTesting constraint application...")
    original_points = bezier.points.copy()
    
    # Move a control point and check if constraints are applied
    bezier._set_point(1, QPointF(2, 2))  # Move control1
    print(f"Points changed: {bezier.points != original_points}")
    
    print("CubicBezierCadItem state cycling test completed successfully!")

if __name__ == "__main__":
    test_cubic_bezier_states() 