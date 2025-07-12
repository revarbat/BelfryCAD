#!/usr/bin/env python3
"""
Test script for state transitions in CubicBezierCadItem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from ..src.BelfryCAD.gui.views.graphics_items.caditems.cubic_bezier_cad_item import CubicBezierCadItem, PathPointState
import math


def test_state_transitions():
    """Test state transition constraints."""
    print("Testing state transitions...")
    
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
    
    # Test 1: SMOOTH to EQUIDISTANT transition
    print("\nTest 1: SMOOTH to EQUIDISTANT transition")
    bezier.set_path_point_state(1, PathPointState.SMOOTH)  # Path point 1
    
    # Get initial distances
    path_point = bezier.points[3]
    prev_control = bezier.points[2]
    next_control = bezier.points[4]
    
    prev_vector = prev_control - path_point
    next_vector = next_control - path_point
    initial_prev_distance = math.sqrt(prev_vector.x()**2 + prev_vector.y()**2)
    initial_next_distance = math.sqrt(next_vector.x()**2 + next_vector.y()**2)
    
    print(f"Initial distances: prev={initial_prev_distance:.3f}, next={initial_next_distance:.3f}")
    
    # Cycle to EQUIDISTANT
    bezier._cycle_path_point_state(3)  # Use point index, not path point index
    
    # Check that distances are now equal
    new_path_point = bezier.points[3]
    new_prev_control = bezier.points[2]
    new_next_control = bezier.points[4]
    
    new_prev_vector = new_prev_control - new_path_point
    new_next_vector = new_next_control - new_path_point
    new_prev_distance = math.sqrt(new_prev_vector.x()**2 + new_prev_vector.y()**2)
    new_next_distance = math.sqrt(new_next_vector.x()**2 + new_next_vector.y()**2)
    
    distance_diff = abs(new_prev_distance - new_next_distance)
    if distance_diff < 0.01:
        print("✓ SMOOTH to EQUIDISTANT: Distances are now equal")
    else:
        print(f"✗ SMOOTH to EQUIDISTANT: Distances are not equal. Diff: {distance_diff:.3f}")
    
    print(f"New distances: prev={new_prev_distance:.3f}, next={new_next_distance:.3f}")
    
    # Test 2: DISJOINT to SMOOTH transition
    print("\nTest 2: DISJOINT to SMOOTH transition")
    # First set to DISJOINT and move control points to different angles
    bezier.set_path_point_state(1, PathPointState.DISJOINT)
    
    # Move control points to different angles
    bezier._set_point(2, QPointF(2.5, 0.5))  # Move prev control
    bezier._set_point(4, QPointF(4.5, -0.5))  # Move next control
    
    # Get angles before transition
    path_point = bezier.points[3]
    prev_control = bezier.points[2]
    next_control = bezier.points[4]
    
    prev_vector = prev_control - path_point
    next_vector = next_control - path_point
    before_prev_angle = math.atan2(prev_vector.y(), prev_vector.x())
    before_next_angle = math.atan2(next_vector.y(), next_vector.x())
    
    print(f"Before transition angles: prev={math.degrees(before_prev_angle):.1f}°, next={math.degrees(before_next_angle):.1f}°")
    
    # Cycle to SMOOTH
    bezier._cycle_path_point_state(3)
    
    # Check that angles are now opposite
    new_path_point = bezier.points[3]
    new_prev_control = bezier.points[2]
    new_next_control = bezier.points[4]
    
    new_prev_vector = new_prev_control - new_path_point
    new_next_vector = new_next_control - new_path_point
    new_prev_angle = math.atan2(new_prev_vector.y(), new_prev_vector.x())
    new_next_angle = math.atan2(new_next_vector.y(), new_next_vector.x())
    
    def normalize_angle(angle):
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    angle_diff = abs(normalize_angle(new_next_angle - (new_prev_angle + math.pi)))
    if angle_diff < 0.1:  # Allow small floating point errors
        print("✓ DISJOINT to SMOOTH: Angles are now opposite (180° apart)")
    else:
        print(f"✗ DISJOINT to SMOOTH: Angles are not opposite. Diff: {math.degrees(angle_diff):.1f}°")
    
    print(f"After transition angles: prev={math.degrees(new_prev_angle):.1f}°, next={math.degrees(new_next_angle):.1f}°")
    
    print("All state transition tests completed!")


if __name__ == "__main__":
    test_state_transitions() 