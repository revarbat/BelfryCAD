#!/usr/bin/env python3
"""
Test script for control point angle adjustment in CubicBezierCadItem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from BelfryCAD.gui.caditems.cubic_bezier_cad_item import CubicBezierCadItem, PathPointState
import math


def test_control_point_angle_adjustment():
    """Test the control point angle adjustment functionality."""
    print("Testing control point angle adjustment...")
    
    # Create a simple cubic Bezier curve with 3 segments
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
    
    # Test 1: Set path point 1 to SMOOTH state and move control point
    print("\nTest 1: SMOOTH state angle adjustment")
    bezier.set_path_point_state(1, PathPointState.SMOOTH)  # Path point index 1 (at points[3])
    
    # Get initial angles
    path_point = bezier.points[3]
    prev_control = bezier.points[2]  # Control 2 of segment 0
    next_control = bezier.points[4]  # Control 1 of segment 1
    
    prev_vector = prev_control - path_point
    next_vector = next_control - path_point
    initial_prev_angle = math.atan2(prev_vector.y(), prev_vector.x())
    initial_next_angle = math.atan2(next_vector.y(), next_vector.x())
    
    print(f"Initial angles: prev={math.degrees(initial_prev_angle):.1f}°, next={math.degrees(initial_next_angle):.1f}°")
    print(f"Initial positions: prev={prev_control}, next={next_control}")
    
    # Move the previous control point
    new_prev_control = QPointF(2.5, -0.5)  # Move it to a new position
    print(f"Moving prev control from {prev_control} to {new_prev_control}")
    bezier._set_point(2, new_prev_control)
    
    # Check that the next control point maintains opposite angle
    new_path_point = bezier.points[3]
    new_prev_control = bezier.points[2]
    new_next_control = bezier.points[4]
    
    print(f"After move: prev={new_prev_control}, next={new_next_control}")
    
    new_prev_vector = new_prev_control - new_path_point
    new_next_vector = new_next_control - new_path_point
    new_prev_angle = math.atan2(new_prev_vector.y(), new_prev_vector.x())
    new_next_angle = math.atan2(new_next_vector.y(), new_next_vector.x())
    
    angle_diff = abs(new_next_angle - (new_prev_angle + math.pi))
    if angle_diff < 0.1:  # Allow small floating point errors
        print("✓ SMOOTH state: Angles are opposite (180° apart)")
    else:
        print(f"✗ SMOOTH state: Angles are not opposite. Diff: {math.degrees(angle_diff):.1f}°")
    
    print(f"New angles: prev={math.degrees(new_prev_angle):.1f}°, next={math.degrees(new_next_angle):.1f}°")
    
    # Test 2: Set path point 1 to EQUIDISTANT state and move control point
    print("\nTest 2: EQUIDISTANT state angle and distance adjustment")
    bezier.set_path_point_state(1, PathPointState.EQUIDISTANT)  # Path point index 1 (at points[3])
    
    # Move the next control point
    new_next_control = QPointF(4.5, 0.5)  # Move it to a new position
    print(f"Moving next control to {new_next_control}")
    bezier._set_point(4, new_next_control)
    
    # Check that both control points have opposite angles and equal distances
    final_path_point = bezier.points[3]
    final_prev_control = bezier.points[2]
    final_next_control = bezier.points[4]
    
    print(f"Final positions: prev={final_prev_control}, next={final_next_control}")
    
    final_prev_vector = final_prev_control - final_path_point
    final_next_vector = final_next_control - final_path_point
    final_prev_angle = math.atan2(final_prev_vector.y(), final_prev_vector.x())
    final_next_angle = math.atan2(final_next_vector.y(), final_next_vector.x())
    
    final_prev_distance = math.sqrt(final_prev_vector.x()**2 + final_prev_vector.y()**2)
    final_next_distance = math.sqrt(final_next_vector.x()**2 + final_next_vector.y()**2)
    
    angle_diff = abs(final_next_angle - (final_prev_angle + math.pi))
    distance_diff = abs(final_prev_distance - final_next_distance)
    
    if angle_diff < 0.1 and distance_diff < 0.01:
        print("✓ EQUIDISTANT state: Angles are opposite and distances are equal")
    else:
        print(f"✗ EQUIDISTANT state: Angle diff: {math.degrees(angle_diff):.1f}°, Distance diff: {distance_diff:.3f}")
    
    print(f"Final angles: prev={math.degrees(final_prev_angle):.1f}°, next={math.degrees(final_next_angle):.1f}°")
    print(f"Final distances: prev={final_prev_distance:.3f}, next={final_next_distance:.3f}")
    
    # Test 3: DISJOINT state should not apply constraints
    print("\nTest 3: DISJOINT state (no constraints)")
    print(f"Setting path point {1} to DISJOINT state")
    bezier.set_path_point_state(1, PathPointState.DISJOINT)  # Path point index 1 (at points[3])
    print(f"Path point state after setting: {bezier.get_path_point_state(1)}")
    
    # Store current positions
    before_prev = bezier.points[2]
    before_next = bezier.points[4]
    print(f"Before move: prev={before_prev}, next={before_next}")
    
    # Move a control point
    print(f"Moving control point 2 to {QPointF(2.8, -0.8)}")
    bezier._set_point(2, QPointF(2.8, -0.8))
    
    # Check that the other control point was NOT adjusted
    after_prev = bezier.points[2]
    after_next = bezier.points[4]
    print(f"After move: prev={after_prev}, next={after_next}")
    
    if before_next == after_next:
        print("✓ DISJOINT state: Other control point was not adjusted")
    else:
        print("✗ DISJOINT state: Other control point was unexpectedly adjusted")
        print(f"  Changed from {before_next} to {after_next}")
    
    print("All tests completed!")


if __name__ == "__main__":
    test_control_point_angle_adjustment() 