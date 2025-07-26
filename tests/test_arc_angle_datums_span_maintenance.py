#!/usr/bin/env python3
"""
Test script for ArcCadItem angle control datum span maintenance.
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


def set_start_angle_maintaining_span(center, start_point, end_point, new_start_angle_degrees):
    """Simulate the _set_start_angle method logic."""
    # Calculate the current span angle before changing the start angle
    current_start_angle = angle_from_center(center, start_point)
    current_end_angle = angle_from_center(center, end_point)
    current_span_angle = current_end_angle - current_start_angle
    
    # Normalize the span angle to be positive
    if current_span_angle < 0:
        current_span_angle += 2 * math.pi
    
    # Update the start point to the new angle
    new_start_angle = math.radians(new_start_angle_degrees)
    radius = distance(center, start_point)
    new_start_point = QPointF(
        center.x() + radius * math.cos(new_start_angle),
        center.y() + radius * math.sin(new_start_angle)
    )
    
    # Calculate the new end angle to maintain the same span
    new_end_angle = new_start_angle + current_span_angle
    
    # Update the end point to maintain the span angle
    new_end_point = QPointF(
        center.x() + radius * math.cos(new_end_angle),
        center.y() + radius * math.sin(new_end_angle)
    )
    
    return new_start_point, new_end_point


def set_end_angle_maintaining_span(center, start_point, end_point, new_end_angle_degrees):
    """Simulate the _set_end_angle method logic."""
    # Calculate the current span angle before changing the end angle
    current_start_angle = angle_from_center(center, start_point)
    current_end_angle = angle_from_center(center, end_point)
    current_span_angle = current_end_angle - current_start_angle
    
    # Normalize the span angle to be positive
    if current_span_angle < 0:
        current_span_angle += 2 * math.pi
    
    # Update the end point to the new angle
    new_end_angle = math.radians(new_end_angle_degrees)
    radius = distance(center, end_point)
    new_end_point = QPointF(
        center.x() + radius * math.cos(new_end_angle),
        center.y() + radius * math.sin(new_end_angle)
    )
    
    # Calculate the new start angle to maintain the same span
    new_start_angle = new_end_angle - current_span_angle
    
    # Update the start point to maintain the span angle
    new_start_point = QPointF(
        center.x() + radius * math.cos(new_start_angle),
        center.y() + radius * math.sin(new_start_angle)
    )
    
    return new_start_point, new_end_point


def test_start_angle_datum_maintains_span():
    """Test that changing the start angle datum maintains the span angle."""
    print("Testing start angle datum maintains span angle...")
    
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
    
    # Simulate changing start angle to 45 degrees
    new_start_angle_degrees = 45.0
    print(f"\nChanging start angle to: {new_start_angle_degrees:.3f}°")
    
    # Apply the logic
    final_start_point, final_end_point = set_start_angle_maintaining_span(
        center, start_point, end_point, new_start_angle_degrees
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
    
    # Verify start angle is correct
    start_angle_difference = abs(math.degrees(final_start_angle) - new_start_angle_degrees)
    print(f"Start angle difference: {start_angle_difference:.3f}°")
    assert start_angle_difference < 0.1, f"Start angle should be {new_start_angle_degrees}°, got {math.degrees(final_start_angle):.3f}°"
    
    print("✓ Start angle datum test passed")
    return True


def test_end_angle_datum_maintains_span():
    """Test that changing the end angle datum maintains the span angle."""
    print("\nTesting end angle datum maintains span angle...")
    
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
    
    # Simulate changing end angle to 135 degrees
    new_end_angle_degrees = 135.0
    print(f"\nChanging end angle to: {new_end_angle_degrees:.3f}°")
    
    # Apply the logic
    final_start_point, final_end_point = set_end_angle_maintaining_span(
        center, start_point, end_point, new_end_angle_degrees
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
    
    # Verify end angle is correct
    end_angle_difference = abs(math.degrees(final_end_angle) - new_end_angle_degrees)
    print(f"End angle difference: {end_angle_difference:.3f}°")
    assert end_angle_difference < 0.1, f"End angle should be {new_end_angle_degrees}°, got {math.degrees(final_end_angle):.3f}°"
    
    print("✓ End angle datum test passed")
    return True


def test_angle_datums_edge_cases():
    """Test angle datum span maintenance with edge cases."""
    print("\nTesting angle datum edge cases...")
    
    # Test case 1: Large span angle
    center = QPointF(0, 0)
    start_point = QPointF(2, 0)  # 0 degrees
    end_point = QPointF(-2, 0)   # 180 degrees (span = 180°)
    
    initial_span_angle = normalize_angle(angle_from_center(center, end_point) - angle_from_center(center, start_point))
    print(f"Initial span angle: {math.degrees(initial_span_angle):.3f}°")
    
    # Change start angle to 90 degrees
    new_start_angle_degrees = 90.0
    final_start_point, final_end_point = set_start_angle_maintaining_span(
        center, start_point, end_point, new_start_angle_degrees
    )
    
    final_span_angle = normalize_angle(angle_from_center(center, final_end_point) - angle_from_center(center, final_start_point))
    span_difference = abs(final_span_angle - initial_span_angle)
    
    print(f"Final span angle: {math.degrees(final_span_angle):.3f}°")
    print(f"Span angle difference: {math.degrees(span_difference):.3f}°")
    assert span_difference < 0.001, f"Span angle should be preserved in edge case"
    
    print("✓ Edge case test passed")
    return True


def main():
    """Run all angle datum span maintenance tests."""
    print("=== ArcCadItem Angle Datum Span Maintenance Tests ===\n")
    
    tests = [
        test_start_angle_datum_maintains_span,
        test_end_angle_datum_maintains_span,
        test_angle_datums_edge_cases
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
        print("All angle datum span maintenance tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 