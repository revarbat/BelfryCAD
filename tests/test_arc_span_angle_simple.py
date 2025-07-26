#!/usr/bin/env python3
"""
Simple test for arc span angle maintenance logic.
"""

import math
from PySide6.QtCore import QPointF


def angle_from_center(center, point):
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


def set_start_maintaining_span(center, start_point, end_point, new_start_point):
    """Simulate the _set_start method logic."""
    # Calculate the current span angle before moving the start point
    current_start_angle = angle_from_center(center, start_point)
    current_end_angle = angle_from_center(center, end_point)
    current_span_angle = current_end_angle - current_start_angle
    
    # Normalize the span angle to be positive
    if current_span_angle < 0:
        current_span_angle += 2 * math.pi
    
    # Calculate the new start angle
    new_start_angle = angle_from_center(center, new_start_point)
    
    # Calculate the new end angle to maintain the same span
    new_end_angle = new_start_angle + current_span_angle
    
    # Calculate the new radius (use the distance from center to new start point)
    new_radius = distance(center, new_start_point)
    
    # Calculate new end point
    new_end_point = QPointF(
        center.x() + new_radius * math.cos(new_end_angle),
        center.y() + new_radius * math.sin(new_end_angle)
    )
    
    return new_start_point, new_end_point


def set_end_maintaining_span(center, start_point, end_point, new_end_point):
    """Simulate the _set_end method logic."""
    # Calculate the current span angle before moving the end point
    current_start_angle = angle_from_center(center, start_point)
    current_end_angle = angle_from_center(center, end_point)
    current_span_angle = current_end_angle - current_start_angle
    
    # Normalize the span angle to be positive
    if current_span_angle < 0:
        current_span_angle += 2 * math.pi
    
    # Calculate the new end angle
    new_end_angle = angle_from_center(center, new_end_point)
    
    # Calculate the new start angle to maintain the same span
    new_start_angle = new_end_angle - current_span_angle
    
    # Calculate the new radius (use the distance from center to new end point)
    new_radius = distance(center, new_end_point)
    
    # Calculate new start point
    new_start_point = QPointF(
        center.x() + new_radius * math.cos(new_start_angle),
        center.y() + new_radius * math.sin(new_start_angle)
    )
    
    return new_start_point, new_end_point


def test_start_point_movement():
    """Test start point movement maintaining span angle."""
    print("Testing start point movement maintains span angle...")
    
    # Initial arc setup
    center = QPointF(0, 0)
    start_point = QPointF(2, 0)  # 0 degrees
    end_point = QPointF(0, 2)    # 90 degrees
    
    # Calculate initial properties
    initial_start_angle = angle_from_center(center, start_point)
    initial_end_angle = angle_from_center(center, end_point)
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
    
    # Apply the logic
    final_start_point, final_end_point = set_start_maintaining_span(
        center, start_point, end_point, new_start_point
    )
    
    print(f"Final start point: ({final_start_point.x():.3f}, {final_start_point.y():.3f})")
    print(f"Final end point: ({final_end_point.x():.3f}, {final_end_point.y():.3f})")
    
    # Verify the results
    final_start_angle = angle_from_center(center, final_start_point)
    final_end_angle = angle_from_center(center, final_end_point)
    final_span_angle = normalize_angle(final_end_angle - final_start_angle)
    
    print(f"Final start angle: {math.degrees(final_start_angle):.3f}°")
    print(f"Final end angle: {math.degrees(final_end_angle):.3f}°")
    print(f"Final span angle: {math.degrees(final_span_angle):.3f}°")
    
    # Verify span angle is preserved
    span_difference = abs(final_span_angle - initial_span_angle)
    print(f"Span angle difference: {math.degrees(span_difference):.3f}°")
    assert span_difference < 0.001, f"Span angle should be preserved, difference: {math.degrees(span_difference):.3f}°"
    
    # Verify radius is consistent
    start_radius = distance(center, final_start_point)
    end_radius = distance(center, final_end_point)
    radius_difference = abs(start_radius - end_radius)
    print(f"Radius difference: {radius_difference:.3f}")
    assert radius_difference < 0.001, f"Radius should be consistent, difference: {radius_difference:.3f}"
    
    print("✓ Start point movement test passed")
    return True


def test_end_point_movement():
    """Test end point movement maintaining span angle."""
    print("\nTesting end point movement maintains span angle...")
    
    # Initial arc setup
    center = QPointF(0, 0)
    start_point = QPointF(2, 0)  # 0 degrees
    end_point = QPointF(0, 2)    # 90 degrees
    
    # Calculate initial properties
    initial_start_angle = angle_from_center(center, start_point)
    initial_end_angle = angle_from_center(center, end_point)
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
    
    # Apply the logic
    final_start_point, final_end_point = set_end_maintaining_span(
        center, start_point, end_point, new_end_point
    )
    
    print(f"Final start point: ({final_start_point.x():.3f}, {final_start_point.y():.3f})")
    print(f"Final end point: ({final_end_point.x():.3f}, {final_end_point.y():.3f})")
    
    # Verify the results
    final_start_angle = angle_from_center(center, final_start_point)
    final_end_angle = angle_from_center(center, final_end_point)
    final_span_angle = normalize_angle(final_end_angle - final_start_angle)
    
    print(f"Final start angle: {math.degrees(final_start_angle):.3f}°")
    print(f"Final end angle: {math.degrees(final_end_angle):.3f}°")
    print(f"Final span angle: {math.degrees(final_span_angle):.3f}°")
    
    # Verify span angle is preserved
    span_difference = abs(final_span_angle - initial_span_angle)
    print(f"Span angle difference: {math.degrees(span_difference):.3f}°")
    assert span_difference < 0.001, f"Span angle should be preserved, difference: {math.degrees(span_difference):.3f}°"
    
    # Verify radius is consistent
    start_radius = distance(center, final_start_point)
    end_radius = distance(center, final_end_point)
    radius_difference = abs(start_radius - end_radius)
    print(f"Radius difference: {radius_difference:.3f}")
    assert radius_difference < 0.001, f"Radius should be consistent, difference: {radius_difference:.3f}"
    
    print("✓ End point movement test passed")
    return True


def main():
    """Run all span angle maintenance tests."""
    print("=== Arc Span Angle Maintenance Logic Tests ===\n")
    
    tests = [
        test_start_point_movement,
        test_end_point_movement
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
        print("All span angle maintenance logic tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 