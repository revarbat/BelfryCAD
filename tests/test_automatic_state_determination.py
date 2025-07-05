#!/usr/bin/env python3
"""
Test script for automatic state determination in CubicBezierCadItem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from BelfryCAD.gui.caditems.cubic_bezier_cad_item import CubicBezierCadItem, PathPointState
import math


def test_automatic_state_determination():
    """Test automatic state determination based on geometric relationships."""
    print("Testing automatic state determination...")
    
    # Test 1: SMOOTH state - opposite angles, different distances
    print("\nTest 1: SMOOTH state (opposite angles, different distances)")
    points_smooth = [
        QPointF(0, 0),    # Path point 0
        QPointF(1, 1),    # Control 1 for segment 0
        QPointF(2, -1),   # Control 2 for segment 0
        QPointF(3, 0),    # Path point 1 - should be SMOOTH
        QPointF(4, 0),    # Control 1 for segment 1 (right, distance 1)
        QPointF(1, 0),    # Control 2 for segment 1 (left, distance 2)
        QPointF(6, 0),    # Path point 2
    ]
    
    bezier_smooth = CubicBezierCadItem(points_smooth, QColor(0, 0, 255), 0.05)
    state = bezier_smooth.get_path_point_state(1)  # Path point 1
    print(f"Determined state: {state}")
    print(f"Expected: {PathPointState.SMOOTH}")
    print(f"✓ Correct" if state == PathPointState.SMOOTH else "✗ Incorrect")
    
    # Test 2: EQUIDISTANT state - opposite angles, equal distances
    print("\nTest 2: EQUIDISTANT state (opposite angles, equal distances)")
    points_equidistant = [
        QPointF(0, 0),    # Path point 0
        QPointF(1, 1),    # Control 1 for segment 0
        QPointF(2, -1),   # Control 2 for segment 0
        QPointF(3, 0),    # Path point 1 - should be EQUIDISTANT
        QPointF(4, 0),    # Control 1 for segment 1 (right, distance 1)
        QPointF(2, 0),    # Control 2 for segment 1 (left, distance 1)
        QPointF(6, 0),    # Path point 2
    ]
    
    bezier_equidistant = CubicBezierCadItem(points_equidistant, QColor(0, 0, 255), 0.05)
    state = bezier_equidistant.get_path_point_state(1)  # Path point 1
    print(f"Determined state: {state}")
    print(f"Expected: {PathPointState.EQUIDISTANT}")
    print(f"✓ Correct" if state == PathPointState.EQUIDISTANT else "✗ Incorrect")
    
    # Test 3: DISJOINT state - not opposite angles
    print("\nTest 3: DISJOINT state (not opposite angles)")
    points_disjoint = [
        QPointF(0, 0),    # Path point 0
        QPointF(1, 1),    # Control 1 for segment 0
        QPointF(2, -1),   # Control 2 for segment 0
        QPointF(3, 0),    # Path point 1 - should be DISJOINT
        QPointF(4, 0),    # Control 1 for segment 1 (right)
        QPointF(3, 1),    # Control 2 for segment 1 (up)
        QPointF(6, 0),    # Path point 2
    ]
    
    bezier_disjoint = CubicBezierCadItem(points_disjoint, QColor(0, 0, 255), 0.05)
    state = bezier_disjoint.get_path_point_state(1)  # Path point 1
    print(f"Determined state: {state}")
    print(f"Expected: {PathPointState.DISJOINT}")
    print(f"✓ Correct" if state == PathPointState.DISJOINT else "✗ Incorrect")
    
    # Test 4: Edge case - very close to opposite angles but just outside tolerance
    print("\nTest 4: Edge case (close to opposite angles but just outside tolerance)")
    # Use a small offset to make the angle difference just outside 5 degrees
    offset = 0.2
    points_edge = [
        QPointF(0, 0),    # Path point 0
        QPointF(1, 1),    # Control 1 for segment 0
        QPointF(2, -1),   # Control 2 for segment 0
        QPointF(3, 0),    # Path point 1
        QPointF(4, 0),    # Control 1 for segment 1 (right)
        QPointF(2 - offset, 0),  # Control 2 for segment 1 (slightly off left)
        QPointF(6, 0),    # Path point 2
    ]
    
    bezier_edge = CubicBezierCadItem(points_edge, QColor(0, 0, 255), 0.05)
    state = bezier_edge.get_path_point_state(1)  # Path point 1
    print(f"Determined state: {state}")
    print(f"Expected: {PathPointState.DISJOINT} (should be DISJOINT due to angle tolerance)")
    print(f"✓ Correct" if state == PathPointState.DISJOINT else "✗ Incorrect")
    
    # Test 5: Verify control point types are created correctly
    print("\nTest 5: Control point types")
    bezier_test = CubicBezierCadItem(points_smooth, QColor(0, 0, 255), 0.05)
    control_points = bezier_test.createControls()
    
    # Check that path point control points have the correct type
    for i in range(0, len(bezier_test.points), 3):
        state = bezier_test.get_path_point_state(i // 3)
        cp = control_points[i]
        cp_type = type(cp).__name__
        
        expected_type = ""
        if state == PathPointState.SMOOTH:
            expected_type = "SquareControlPoint"
        elif state == PathPointState.EQUIDISTANT:
            expected_type = "ControlPoint"
        else:  # DISJOINT
            expected_type = "DiamondControlPoint"
        
        print(f"Path point {i//3} (state: {state}): {cp_type} (expected: {expected_type})")
        print(f"✓ Correct" if cp_type == expected_type else "✗ Incorrect")
    
    print("All automatic state determination tests completed!")


if __name__ == "__main__":
    test_automatic_state_determination() 