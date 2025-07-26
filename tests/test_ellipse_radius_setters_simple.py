#!/usr/bin/env python3
"""
Simple test for EllipseCadItem radius setter methods.
"""

import math
from PySide6.QtCore import QPointF


def test_major_radius_setter_simple():
    """Test that setting major radius works correctly."""
    print("Testing major radius setter...")
    
    # Initial ellipse setup
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    # Calculate initial properties
    center = (focus1 + focus2) * 0.5
    major_radius_initial = 3.0
    minor_radius_initial = 2.236
    
    print(f"Initial major radius: {major_radius_initial:.3f}")
    print(f"Initial minor radius: {minor_radius_initial:.3f}")
    
    # Simulate setting major radius to 5.0
    new_major_radius = 5.0
    print(f"\nSetting major radius to: {new_major_radius:.3f}")
    
    # Step 1: Calculate new focal distance
    new_focal_distance = math.sqrt(new_major_radius * new_major_radius - 
                                 minor_radius_initial * minor_radius_initial)
    print(f"New focal distance: {new_focal_distance:.3f}")
    
    # Step 2: Scale the foci distance
    current_focal_distance = math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2
    scale_factor = new_focal_distance / current_focal_distance
    focus1_relative = focus1 - center
    focus2_relative = focus2 - center
    new_focus1 = center + focus1_relative * scale_factor
    new_focus2 = center + focus2_relative * scale_factor
    
    print(f"New focus1: ({new_focus1.x():.3f}, {new_focus1.y():.3f})")
    print(f"New focus2: ({new_focus2.x():.3f}, {new_focus2.y():.3f})")
    
    # Step 3: Set perimeter point along major axis
    major_axis_direction = new_focus2 - center
    major_axis_length = math.hypot(major_axis_direction.x(), major_axis_direction.y())
    if major_axis_length > 0:
        major_axis_direction = QPointF(major_axis_direction.x() / major_axis_length,
                                     major_axis_direction.y() / major_axis_length)
    
    new_perimeter = center + QPointF(major_axis_direction.x() * new_major_radius,
                                    major_axis_direction.y() * new_major_radius)
    
    print(f"New perimeter: ({new_perimeter.x():.3f}, {new_perimeter.y():.3f})")
    
    # Verify the results
    final_dist1 = math.hypot(new_perimeter.x() - new_focus1.x(), new_perimeter.y() - new_focus1.y())
    final_dist2 = math.hypot(new_perimeter.x() - new_focus2.x(), new_perimeter.y() - new_focus2.y())
    final_major_radius = (final_dist1 + final_dist2) / 2
    final_focal_distance = math.hypot(new_focus2.x() - new_focus1.x(), new_focus2.y() - new_focus1.y()) / 2
    final_minor_radius = math.sqrt(final_major_radius * final_major_radius - final_focal_distance * final_focal_distance)
    
    print(f"Final major radius: {final_major_radius:.3f}")
    print(f"Final minor radius: {final_minor_radius:.3f}")
    print(f"Final focal distance: {final_focal_distance:.3f}")
    
    # Verify major radius is correct
    assert abs(final_major_radius - new_major_radius) < 0.001, f"Major radius should be {new_major_radius}, got {final_major_radius}"
    
    print("✓ Major radius setter test passed")
    return True


def test_minor_radius_setter_simple():
    """Test that setting minor radius works correctly."""
    print("\nTesting minor radius setter...")
    
    # Initial ellipse setup
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    # Calculate initial properties
    center = (focus1 + focus2) * 0.5
    major_radius_initial = 3.0
    minor_radius_initial = 2.236
    
    print(f"Initial major radius: {major_radius_initial:.3f}")
    print(f"Initial minor radius: {minor_radius_initial:.3f}")
    
    # Simulate setting minor radius to 1.5
    new_minor_radius = 1.5
    print(f"\nSetting minor radius to: {new_minor_radius:.3f}")
    
    # Step 1: Calculate new focal distance
    new_focal_distance = math.sqrt(major_radius_initial * major_radius_initial - 
                                 new_minor_radius * new_minor_radius)
    print(f"New focal distance: {new_focal_distance:.3f}")
    
    # Step 2: Scale the foci distance
    current_focal_distance = math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2
    scale_factor = new_focal_distance / current_focal_distance
    focus1_relative = focus1 - center
    focus2_relative = focus2 - center
    new_focus1 = center + focus1_relative * scale_factor
    new_focus2 = center + focus2_relative * scale_factor
    
    print(f"New focus1: ({new_focus1.x():.3f}, {new_focus1.y():.3f})")
    print(f"New focus2: ({new_focus2.x():.3f}, {new_focus2.y():.3f})")
    
    # Step 3: Set perimeter point along major axis to maintain original major radius
    major_axis_direction = new_focus2 - center
    major_axis_length = math.hypot(major_axis_direction.x(), major_axis_direction.y())
    if major_axis_length > 0:
        major_axis_direction = QPointF(major_axis_direction.x() / major_axis_length,
                                     major_axis_direction.y() / major_axis_length)
    
    new_perimeter = center + QPointF(major_axis_direction.x() * major_radius_initial,
                                    major_axis_direction.y() * major_radius_initial)
    
    print(f"New perimeter: ({new_perimeter.x():.3f}, {new_perimeter.y():.3f})")
    
    # Verify the results
    final_dist1 = math.hypot(new_perimeter.x() - new_focus1.x(), new_perimeter.y() - new_focus1.y())
    final_dist2 = math.hypot(new_perimeter.x() - new_focus2.x(), new_perimeter.y() - new_focus2.y())
    final_major_radius = (final_dist1 + final_dist2) / 2
    final_focal_distance = math.hypot(new_focus2.x() - new_focus1.x(), new_focus2.y() - new_focus1.y()) / 2
    final_minor_radius = math.sqrt(final_major_radius * final_major_radius - final_focal_distance * final_focal_distance)
    
    print(f"Final major radius: {final_major_radius:.3f}")
    print(f"Final minor radius: {final_minor_radius:.3f}")
    print(f"Final focal distance: {final_focal_distance:.3f}")
    
    # Verify minor radius is correct
    assert abs(final_minor_radius - new_minor_radius) < 0.001, f"Minor radius should be {new_minor_radius}, got {final_minor_radius}"
    
    # Verify major radius is preserved
    assert abs(final_major_radius - major_radius_initial) < 0.001, f"Major radius should be preserved, got {final_major_radius}"
    
    print("✓ Minor radius setter test passed")
    return True


def main():
    """Run all simple radius setter tests."""
    print("=== Simple EllipseCadItem Radius Setter Tests ===\n")
    
    tests = [
        test_major_radius_setter_simple,
        test_minor_radius_setter_simple
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
        print("All simple radius setter tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 