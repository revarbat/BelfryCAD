#!/usr/bin/env python3
"""
Test script for ArcCadItem span angle maintenance.
"""

import math
from PySide6.QtCore import QPointF


def test_start_point_movement_maintains_span():
    """Test that moving the start point maintains the span angle."""
    print("Testing start point movement maintains span angle...")
    
    # Initial arc setup
    center = QPointF(0, 0)
    start_point = QPointF(2, 0)  # 0 degrees
    end_point = QPointF(0, 2)    # 90 degrees
    
    # Calculate initial properties
    def angle_from_center(point):
        """Calculate angle from center to point in radians."""
        return math.atan2(point.y() - center.y(), point.x() - center.x())
    
    def distance(point1, point2):
        """Calculate distance between two points."""
        return math.hypot(point2.x() - point1.x(), point2.y() - point1.y())
    
    def normalize_angle(angle):
        """Normalize angle to 0-2π range."""
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        return angle
    
    initial_start_angle = angle_from_center(start_point)
    initial_end_angle = angle_from_center(end_point)
    initial_span_angle = normalize_angle(initial_end_angle - initial_start_angle)
    
    print(f"Initial center: ({center.x():.3f}, {center.y():.3f})")
    print(f"Initial start point: ({start_point.x():.3f}, {start_point.y():.3f})")
    print(f"Initial end point: ({end_point.x():.3f}, {end_point.y():.3f})")
    print(f"Initial start angle: {math.degrees(initial_start_angle):.3f}°")
    print(f"Initial end angle: {math.degrees(initial_end_angle):.3f}°")
    print(f"Initial span angle: {math.degrees(initial_span_angle):.3f}°")
    
    # Simulate moving start point to a new position
    new_start_point = QPointF(1, 1)  # 45 degrees
    print(f"\nMoving start point to: ({new_start_point.x():.3f}, {new_start_point.y():.3f})")
    
    # Calculate new start angle
    new_start_angle = angle_from_center(new_start_point)
    print(f"New start angle: {math.degrees(new_start_angle):.3f}°")
    
    # Calculate new end angle to maintain span
    new_end_angle = new_start_angle + initial_span_angle
    print(f"New end angle: {math.degrees(new_end_angle):.3f}°")
    
    # Calculate new radius
    new_radius = distance(center, new_start_point)
    print(f"New radius: {new_radius:.3f}")
    
    # Calculate new end point
    new_end_point = QPointF(
        center.x() + new_radius * math.cos(new_end_angle),
        center.y() + new_radius * math.sin(new_end_angle)
    )
    print(f"New end point: ({new_end_point.x():.3f}, {new_end_point.y():.3f})")
    
    # Verify the results
    final_start_angle = angle_from_center(new_start_point)
    final_end_angle = angle_from_center(new_end_point)
    final_span_angle = normalize_angle(final_end_angle - final_start_angle)
    
    print(f"Final start angle: {math.degrees(final_start_angle):.3f}°")
    print(f"Final end angle: {math.degrees(final_end_angle):.3f}°")
    print(f"Final span angle: {math.degrees(final_span_angle):.3f}°")
    
    # Verify span angle is preserved
    span_difference = abs(final_span_angle - initial_span_angle)
    print(f"Span angle difference: {math.degrees(span_difference):.3f}°")
    assert span_difference < 0.001, f"Span angle should be preserved, difference: {math.degrees(span_difference):.3f}°"
    
    # Verify radius is consistent
    final_radius = distance(center, new_end_point)
    radius_difference = abs(final_radius - new_radius)
    print(f"Radius difference: {radius_difference:.3f}")
    assert radius_difference < 0.001, f"Radius should be consistent, difference: {radius_difference:.3f}"
    
    print("✓ Start point movement test passed")
    return True


def test_end_point_movement_maintains_span():
    """Test that moving the end point maintains the span angle."""
    print("\nTesting end point movement maintains span angle...")
    
    # Initial arc setup
    center = QPointF(0, 0)
    start_point = QPointF(2, 0)  # 0 degrees
    end_point = QPointF(0, 2)    # 90 degrees
    
    # Calculate initial properties
    def angle_from_center(point):
        """Calculate angle from center to point in radians."""
        return math.atan2(point.y() - center.y(), point.x() - center.x())
    
    def distance(point1, point2):
        """Calculate distance between two points."""
        return math.hypot(point2.x() - point1.x(), point2.y() - point1.y())
    
    def normalize_angle(angle):
        """Normalize angle to 0-2π range."""
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        return angle
    
    initial_start_angle = angle_from_center(start_point)
    initial_end_angle = angle_from_center(end_point)
    initial_span_angle = normalize_angle(initial_end_angle - initial_start_angle)
    
    print(f"Initial center: ({center.x():.3f}, {center.y():.3f})")
    print(f"Initial start point: ({start_point.x():.3f}, {start_point.y():.3f})")
    print(f"Initial end point: ({end_point.x():.3f}, {end_point.y():.3f})")
    print(f"Initial start angle: {math.degrees(initial_start_angle):.3f}°")
    print(f"Initial end angle: {math.degrees(initial_end_angle):.3f}°")
    print(f"Initial span angle: {math.degrees(initial_span_angle):.3f}°")
    
    # Simulate moving end point to a new position
    new_end_point = QPointF(-1, 1)  # 135 degrees
    print(f"\nMoving end point to: ({new_end_point.x():.3f}, {new_end_point.y():.3f})")
    
    # Calculate new end angle
    new_end_angle = angle_from_center(new_end_point)
    print(f"New end angle: {math.degrees(new_end_angle):.3f}°")
    
    # Calculate new start angle to maintain span
    new_start_angle = new_end_angle - initial_span_angle
    print(f"New start angle: {math.degrees(new_start_angle):.3f}°")
    
    # Calculate new radius
    new_radius = distance(center, new_end_point)
    print(f"New radius: {new_radius:.3f}")
    
    # Calculate new start point
    new_start_point = QPointF(
        center.x() + new_radius * math.cos(new_start_angle),
        center.y() + new_radius * math.sin(new_start_angle)
    )
    print(f"New start point: ({new_start_point.x():.3f}, {new_start_point.y():.3f})")
    
    # Verify the results
    final_start_angle = angle_from_center(new_start_point)
    final_end_angle = angle_from_center(new_end_point)
    final_span_angle = normalize_angle(final_end_angle - final_start_angle)
    
    print(f"Final start angle: {math.degrees(final_start_angle):.3f}°")
    print(f"Final end angle: {math.degrees(final_end_angle):.3f}°")
    print(f"Final span angle: {math.degrees(final_span_angle):.3f}°")
    
    # Verify span angle is preserved
    span_difference = abs(final_span_angle - initial_span_angle)
    print(f"Span angle difference: {math.degrees(span_difference):.3f}°")
    assert span_difference < 0.001, f"Span angle should be preserved, difference: {math.degrees(span_difference):.3f}°"
    
    # Verify radius is consistent
    final_radius = distance(center, new_start_point)
    radius_difference = abs(final_radius - new_radius)
    print(f"Radius difference: {radius_difference:.3f}")
    assert radius_difference < 0.001, f"Radius should be consistent, difference: {radius_difference:.3f}"
    
    print("✓ End point movement test passed")
    return True


def test_span_angle_edge_cases():
    """Test span angle maintenance with edge cases."""
    print("\nTesting span angle edge cases...")
    
    # Test case 1: Span angle crossing 0 degrees
    center = QPointF(0, 0)
    start_point = QPointF(2, 0)  # 0 degrees
    end_point = QPointF(-2, 0)   # 180 degrees (span = 180°)
    
    def angle_from_center(point):
        return math.atan2(point.y() - center.y(), point.x() - center.x())
    
    def normalize_angle(angle):
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        return angle
    
    initial_span_angle = normalize_angle(angle_from_center(end_point) - angle_from_center(start_point))
    print(f"Initial span angle: {math.degrees(initial_span_angle):.3f}°")
    
    # Move start point to 90 degrees
    new_start_point = QPointF(0, 2)
    new_start_angle = angle_from_center(new_start_point)
    new_end_angle = new_start_angle + initial_span_angle
    
    # Calculate new end point
    new_radius = math.hypot(new_start_point.x() - center.x(), new_start_point.y() - center.y())
    new_end_point = QPointF(
        center.x() + new_radius * math.cos(new_end_angle),
        center.y() + new_radius * math.sin(new_end_angle)
    )
    
    final_span_angle = normalize_angle(angle_from_center(new_end_point) - angle_from_center(new_start_point))
    span_difference = abs(final_span_angle - initial_span_angle)
    
    print(f"Final span angle: {math.degrees(final_span_angle):.3f}°")
    print(f"Span angle difference: {math.degrees(span_difference):.3f}°")
    assert span_difference < 0.001, f"Span angle should be preserved in edge case"
    
    print("✓ Edge case test passed")
    return True


def main():
    """Run all span angle maintenance tests."""
    print("=== ArcCadItem Span Angle Maintenance Tests ===\n")
    
    tests = [
        test_start_point_movement_maintains_span,
        test_end_point_movement_maintains_span,
        test_span_angle_edge_cases
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
        print("All span angle maintenance tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 