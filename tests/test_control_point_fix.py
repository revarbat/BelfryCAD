#!/usr/bin/env python3
"""
Unit test to verify the control point coordinate fix works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from ..src.BelfryCAD.gui.graphics_items.caditems.polyline_cad_item import PolylineCadItem

def test_control_point_coordinates():
    """Test that control point coordinates are handled correctly."""
    
    # Create a polyline with known points
    points = [
        QPointF(0, 0),
        QPointF(100, 0),
        QPointF(100, 100),
        QPointF(0, 100)
    ]
    
    polyline = PolylineCadItem(points, QColor(0, 255, 0), 2.0)
    
    # Test that the polyline has the expected points
    assert len(polyline.points) == 4, f"Expected 4 points, got {len(polyline.points)}"
    assert polyline.points[0] == QPointF(0, 0), f"Expected (0,0), got {polyline.points[0]}"
    assert polyline.points[1] == QPointF(100, 0), f"Expected (100,0), got {polyline.points[1]}"
    assert polyline.points[2] == QPointF(100, 100), f"Expected (100,100), got {polyline.points[2]}"
    assert polyline.points[3] == QPointF(0, 100), f"Expected (0,100), got {polyline.points[3]}"
    
    # Test that control points are created
    control_points = polyline.createControls()
    assert len(control_points) == 4, f"Expected 4 control points, got {len(control_points)}"
    
    # Test that the setter methods work correctly
    # Simulate moving the first control point to a new position
    new_position = QPointF(50, 50)  # This should be in CAD item's local coordinates
    
    # Call the setter directly to test the coordinate conversion
    polyline._set_point(0, new_position)
    
    # The point should now be at the scene coordinates corresponding to (50, 50) in local coordinates
    # Since the polyline is at the origin, local coordinates should equal scene coordinates
    expected_scene_position = polyline.mapToScene(new_position)
    actual_point = polyline.points[0]
    
    print(f"Test results:")
    print(f"  New position (local): {new_position}")
    print(f"  Expected scene position: {expected_scene_position}")
    print(f"  Actual point position: {actual_point}")
    print(f"  Points match: {actual_point == expected_scene_position}")
    
    # The fix ensures that the setter receives coordinates in the CAD item's local coordinate system
    # and converts them to scene coordinates correctly
    assert actual_point == expected_scene_position, f"Coordinate conversion failed: expected {expected_scene_position}, got {actual_point}"
    
    print("✅ Control point coordinate fix test passed!")
    return True

if __name__ == "__main__":
    try:
        test_control_point_coordinates()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1) 