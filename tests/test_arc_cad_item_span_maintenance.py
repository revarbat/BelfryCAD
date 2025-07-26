#!/usr/bin/env python3
"""
Test script for ArcCadItem span angle maintenance using the actual class.
"""

import math
import sys
import os

# Add the src directory to the path so we can import BelfryCAD modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from BelfryCAD.gui.views.graphics_items.caditems.arc_cad_item import ArcCadItem


class MockMainWindow:
    """Mock main window for testing."""
    def __init__(self):
        self.scene = None


def test_arc_cad_item_span_maintenance():
    """Test that ArcCadItem maintains span angle when moving control points."""
    print("Testing ArcCadItem span angle maintenance...")
    
    # Create a mock main window
    mock_main_window = MockMainWindow()
    
    # Create an arc with a 90-degree span
    center = QPointF(0, 0)
    start_point = QPointF(2, 0)  # 0 degrees
    end_point = QPointF(0, 2)    # 90 degrees
    
    arc = ArcCadItem(
        main_window=mock_main_window,
        center_point=center,
        start_point=start_point,
        end_point=end_point
    )
    
    print(f"Initial center: ({arc.center_point.x():.3f}, {arc.center_point.y():.3f})")
    print(f"Initial start point: ({arc.start_point.x():.3f}, {arc.start_point.y():.3f})")
    print(f"Initial end point: ({arc.end_point.x():.3f}, {arc.end_point.y():.3f})")
    print(f"Initial start angle: {arc.start_angle:.3f}°")
    print(f"Initial end angle: {arc.end_angle:.3f}°")
    print(f"Initial span angle: {arc.span_angle:.3f}°")
    
    # Store initial span angle
    initial_span_angle = arc.span_angle
    
    # Test moving the start point
    new_start_point = QPointF(1, 1)  # 45 degrees
    print(f"\nMoving start point to: ({new_start_point.x():.3f}, {new_start_point.y():.3f})")
    
    # Call the setter method directly
    arc._set_start(new_start_point)
    
    print(f"New center: ({arc.center_point.x():.3f}, {arc.center_point.y():.3f})")
    print(f"New start point: ({arc.start_point.x():.3f}, {arc.start_point.y():.3f})")
    print(f"New end point: ({arc.end_point.x():.3f}, {arc.end_point.y():.3f})")
    print(f"New start angle: {arc.start_angle:.3f}°")
    print(f"New end angle: {arc.end_angle:.3f}°")
    print(f"New span angle: {arc.span_angle:.3f}°")
    
    # Verify span angle is preserved
    span_difference = abs(arc.span_angle - initial_span_angle)
    print(f"Span angle difference: {span_difference:.3f}°")
    assert span_difference < 0.1, f"Span angle should be preserved, difference: {span_difference:.3f}°"
    
    # Verify radius is consistent
    start_radius = math.hypot(arc.start_point.x() - arc.center_point.x(), 
                              arc.start_point.y() - arc.center_point.y())
    end_radius = math.hypot(arc.end_point.x() - arc.center_point.x(), 
                            arc.end_point.y() - arc.center_point.y())
    radius_difference = abs(start_radius - end_radius)
    print(f"Radius difference: {radius_difference:.3f}")
    assert radius_difference < 0.1, f"Radius should be consistent, difference: {radius_difference:.3f}"
    
    print("✓ ArcCadItem start point movement test passed")
    return True


def test_arc_cad_item_end_point_movement():
    """Test that ArcCadItem maintains span angle when moving the end point."""
    print("\nTesting ArcCadItem end point movement...")
    
    # Create a mock main window
    mock_main_window = MockMainWindow()
    
    # Create an arc with a 90-degree span
    center = QPointF(0, 0)
    start_point = QPointF(2, 0)  # 0 degrees
    end_point = QPointF(0, 2)    # 90 degrees
    
    arc = ArcCadItem(
        main_window=mock_main_window,
        center_point=center,
        start_point=start_point,
        end_point=end_point
    )
    
    print(f"Initial center: ({arc.center_point.x():.3f}, {arc.center_point.y():.3f})")
    print(f"Initial start point: ({arc.start_point.x():.3f}, {arc.start_point.y():.3f})")
    print(f"Initial end point: ({arc.end_point.x():.3f}, {arc.end_point.y():.3f})")
    print(f"Initial start angle: {arc.start_angle:.3f}°")
    print(f"Initial end angle: {arc.end_angle:.3f}°")
    print(f"Initial span angle: {arc.span_angle:.3f}°")
    
    # Store initial span angle
    initial_span_angle = arc.span_angle
    
    # Test moving the end point
    new_end_point = QPointF(-1, 1)  # 135 degrees
    print(f"\nMoving end point to: ({new_end_point.x():.3f}, {new_end_point.y():.3f})")
    
    # Call the setter method directly
    arc._set_end(new_end_point)
    
    print(f"New center: ({arc.center_point.x():.3f}, {arc.center_point.y():.3f})")
    print(f"New start point: ({arc.start_point.x():.3f}, {arc.start_point.y():.3f})")
    print(f"New end point: ({arc.end_point.x():.3f}, {arc.end_point.y():.3f})")
    print(f"New start angle: {arc.start_angle:.3f}°")
    print(f"New end angle: {arc.end_angle:.3f}°")
    print(f"New span angle: {arc.span_angle:.3f}°")
    
    # Verify span angle is preserved
    span_difference = abs(arc.span_angle - initial_span_angle)
    print(f"Span angle difference: {span_difference:.3f}°")
    assert span_difference < 0.1, f"Span angle should be preserved, difference: {span_difference:.3f}°"
    
    # Verify radius is consistent
    start_radius = math.hypot(arc.start_point.x() - arc.center_point.x(), 
                              arc.start_point.y() - arc.center_point.y())
    end_radius = math.hypot(arc.end_point.x() - arc.center_point.x(), 
                            arc.end_point.y() - arc.center_point.y())
    radius_difference = abs(start_radius - end_radius)
    print(f"Radius difference: {radius_difference:.3f}")
    assert radius_difference < 0.1, f"Radius should be consistent, difference: {radius_difference:.3f}"
    
    print("✓ ArcCadItem end point movement test passed")
    return True


def main():
    """Run all ArcCadItem span angle maintenance tests."""
    print("=== ArcCadItem Span Angle Maintenance Tests ===\n")
    
    tests = [
        test_arc_cad_item_span_maintenance,
        test_arc_cad_item_end_point_movement
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✓ Test passed\n")
            else:
                print("✗ Test failed\n")
        except Exception as e:
            print(f"✗ Test failed with exception: {e}\n")
    
    print(f"=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("All ArcCadItem span angle maintenance tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 