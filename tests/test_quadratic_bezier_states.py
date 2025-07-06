#!/usr/bin/env python3
"""
Test script for state determination in QuadraticBezierCadItem.
"""

import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from ..src.BelfryCAD.gui.graphics_items.caditems.quadratic_bezier_cad_item import QuadraticBezierCadItem, PathPointState


def test_quadratic_bezier_states():
    """Test state determination based on geometric relationships for quadratic Bezier curves."""
    print("Testing quadratic Bezier state determination...")
    
    # Test 1: SMOOTH state - opposite angles, different distances
    print("\nTest 1: SMOOTH state (opposite angles, different distances)")
    points_smooth = [
        QPointF(0, 0),    # Path point 0
        QPointF(1, 0),    # Control point for segment 0
        QPointF(3, 0),    # Path point 1 - should be SMOOTH
        QPointF(5, 0),    # Control point for segment 1 (right, distance 2)
        QPointF(6, 0),    # Path point 2
    ]
    # For SMOOTH, make the left and right distances different
    points_smooth[1] = QPointF(2, 0)  # left, distance 1
    points_smooth[3] = QPointF(5, 0)  # right, distance 2
    
    # Debug print for SMOOTH
    path_point = points_smooth[2]
    prev_control = points_smooth[1]
    next_control = points_smooth[3]
    prev_vector = prev_control - path_point
    next_vector = next_control - path_point
    prev_angle = math.atan2(prev_vector.y(), prev_vector.x())
    next_angle = math.atan2(next_vector.y(), next_vector.x())
    angle_diff = abs(prev_angle - next_angle)
    if angle_diff > math.pi:
        angle_diff = 2 * math.pi - angle_diff
    print(f"[SMOOTH] prev_vector: {prev_vector}, next_vector: {next_vector}")
    print(f"[SMOOTH] prev_angle: {prev_angle}, next_angle: {next_angle}")
    print(f"[SMOOTH] angle_diff: {angle_diff}, |angle_diff - pi|: {abs(angle_diff - math.pi)}")
    prev_distance = math.sqrt(prev_vector.x()**2 + prev_vector.y()**2)
    next_distance = math.sqrt(next_vector.x()**2 + next_vector.y()**2)
    print(f"[SMOOTH] prev_distance: {prev_distance}, next_distance: {next_distance}")
    if prev_distance > 0 and next_distance > 0:
        distance_ratio = min(prev_distance, next_distance) / max(prev_distance, next_distance)
        print(f"[SMOOTH] distance_ratio: {distance_ratio}")
    
    bezier_smooth = QuadraticBezierCadItem(points_smooth, QColor(0, 0, 255), 0.05)
    state = bezier_smooth.get_path_point_state(1)  # Path point 1
    print(f"Determined state: {state}")
    print(f"Expected: {PathPointState.SMOOTH}")
    print(f"✓ Correct" if state == PathPointState.SMOOTH else "✗ Incorrect")
    
    # Test 2: EQUIDISTANT state - opposite angles, equal distances
    print("\nTest 2: EQUIDISTANT state (opposite angles, equal distances)")
    points_equidistant = [
        QPointF(0, 0),    # Path point 0
        QPointF(1, 0),    # Control point for segment 0
        QPointF(3, 0),    # Path point 1 - should be EQUIDISTANT
        QPointF(5, 0),    # Control point for segment 1 (right, distance 2)
        QPointF(6, 0),    # Path point 2
    ]
    # For EQUIDISTANT, both left and right distances are 2
    points_equidistant[1] = QPointF(1, 0)  # left, distance 2
    points_equidistant[3] = QPointF(5, 0)  # right, distance 2
    
    # Debug print for EQUIDISTANT
    path_point = points_equidistant[2]
    prev_control = points_equidistant[1]
    next_control = points_equidistant[3]
    prev_vector = prev_control - path_point
    next_vector = next_control - path_point
    prev_angle = math.atan2(prev_vector.y(), prev_vector.x())
    next_angle = math.atan2(next_vector.y(), next_vector.x())
    angle_diff = abs(prev_angle - next_angle)
    if angle_diff > math.pi:
        angle_diff = 2 * math.pi - angle_diff
    print(f"[EQUIDISTANT] prev_vector: {prev_vector}, next_vector: {next_vector}")
    print(f"[EQUIDISTANT] prev_angle: {prev_angle}, next_angle: {next_angle}")
    print(f"[EQUIDISTANT] angle_diff: {angle_diff}, |angle_diff - pi|: {abs(angle_diff - math.pi)}")
    prev_distance = math.sqrt(prev_vector.x()**2 + prev_vector.y()**2)
    next_distance = math.sqrt(next_vector.x()**2 + next_vector.y()**2)
    print(f"[EQUIDISTANT] prev_distance: {prev_distance}, next_distance: {next_distance}")
    if prev_distance > 0 and next_distance > 0:
        distance_ratio = min(prev_distance, next_distance) / max(prev_distance, next_distance)
        print(f"[EQUIDISTANT] distance_ratio: {distance_ratio}")
    
    bezier_equidistant = QuadraticBezierCadItem(points_equidistant, QColor(0, 0, 255), 0.05)
    state = bezier_equidistant.get_path_point_state(1)  # Path point 1
    print(f"Determined state: {state}")
    print(f"Expected: {PathPointState.EQUIDISTANT}")
    print(f"✓ Correct" if state == PathPointState.EQUIDISTANT else "✗ Incorrect")
    
    # Test 3: DISJOINT state - not opposite angles
    print("\nTest 3: DISJOINT state (not opposite angles)")
    points_disjoint = [
        QPointF(0, 0),    # Path point 0
        QPointF(1, 0),    # Control point for segment 0
        QPointF(3, 0),    # Path point 1 - should be DISJOINT
        QPointF(4, 0),    # Control point for segment 1 (right)
        QPointF(6, 0),    # Path point 2
    ]
    # For DISJOINT, make the control points not opposite
    points_disjoint[1] = QPointF(2, 0)  # left
    points_disjoint[3] = QPointF(3, 1)  # up (not opposite)
    
    bezier_disjoint = QuadraticBezierCadItem(points_disjoint, QColor(0, 0, 255), 0.05)
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
        QPointF(1, 0),    # Control point for segment 0
        QPointF(3, 0),    # Path point 1
        QPointF(5, 0),    # Control point for segment 1 (right)
        QPointF(6, 0),    # Path point 2
    ]
    # Make the left control point slightly off from being opposite
    points_edge[1] = QPointF(1 - offset, 0)  # slightly off left
    
    bezier_edge = QuadraticBezierCadItem(points_edge, QColor(0, 0, 255), 0.05)
    state = bezier_edge.get_path_point_state(1)  # Path point 1
    print(f"Determined state: {state}")
    print(f"Expected: {PathPointState.DISJOINT} (should be DISJOINT due to angle tolerance)")
    print(f"✓ Correct" if state == PathPointState.DISJOINT else "✗ Incorrect")
    
    print("All quadratic Bezier state determination tests completed!")


if __name__ == "__main__":
    test_quadratic_bezier_states() 