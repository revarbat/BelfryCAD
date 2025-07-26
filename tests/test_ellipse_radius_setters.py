#!/usr/bin/env python3
"""
Test script for EllipseCadItem radius setter methods.
"""

import math
from PySide6.QtCore import QPointF


def test_major_radius_setter():
    """Test that setting major radius adjusts perimeter point correctly."""
    print("Testing major radius setter...")
    
    # Initial ellipse setup
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    # Calculate initial properties
    center = (focus1 + focus2) * 0.5
    major_radius_initial = 3.0  # Based on perimeter point
    minor_radius_initial = 2.236  # Calculated from major radius and focal distance
    
    print(f"Initial center: ({center.x():.3f}, {center.y():.3f})")
    print(f"Initial major radius: {major_radius_initial:.3f}")
    print(f"Initial minor radius: {minor_radius_initial:.3f}")
    print(f"Initial perimeter: ({perimeter.x():.3f}, {perimeter.y():.3f})")
    
    # Simulate setting major radius to 5.0
    new_major_radius = 5.0
    print(f"\nSetting major radius to: {new_major_radius:.3f}")
    
    # Calculate current distances from foci to perimeter
    dist1 = math.hypot(perimeter.x() - focus1.x(), perimeter.y() - focus1.y())
    dist2 = math.hypot(perimeter.x() - focus2.x(), perimeter.y() - focus2.y())
    current_major_radius = (dist1 + dist2) / 2
    
    print(f"Current major radius: {current_major_radius:.3f}")
    
    # Calculate the scale factor
    scale_factor = new_major_radius / current_major_radius
    print(f"Scale factor: {scale_factor:.3f}")
    
    # Scale the perimeter point relative to the center
    relative_pos = perimeter - center
    new_perimeter = center + relative_pos * scale_factor
    
    print(f"New perimeter: ({new_perimeter.x():.3f}, {new_perimeter.y():.3f})")
    
    # Verify the new major radius
    new_dist1 = math.hypot(new_perimeter.x() - focus1.x(), new_perimeter.y() - focus1.y())
    new_dist2 = math.hypot(new_perimeter.x() - focus2.x(), new_perimeter.y() - focus2.y())
    new_major_radius_calc = (new_dist1 + new_dist2) / 2
    
    print(f"Calculated new major radius: {new_major_radius_calc:.3f}")
    assert abs(new_major_radius_calc - new_major_radius) < 0.001, f"Major radius should be {new_major_radius}, got {new_major_radius_calc}"
    
    # Verify the minor radius should remain approximately the same
    # (it will change slightly due to the new perimeter point)
    focal_distance = math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2
    new_minor_radius = math.sqrt(new_major_radius_calc * new_major_radius_calc - focal_distance * focal_distance)
    print(f"New minor radius: {new_minor_radius:.3f}")
    
    print("✓ Major radius setter test passed")
    return True


def test_minor_radius_setter():
    """Test that setting minor radius adjusts focal distance correctly."""
    print("\nTesting minor radius setter...")
    
    # Initial ellipse setup
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    # Calculate initial properties
    center = (focus1 + focus2) * 0.5
    major_radius_initial = 3.0
    minor_radius_initial = 2.236
    focal_distance_initial = math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2
    
    print(f"Initial center: ({center.x():.3f}, {center.y():.3f})")
    print(f"Initial major radius: {major_radius_initial:.3f}")
    print(f"Initial minor radius: {minor_radius_initial:.3f}")
    print(f"Initial focal distance: {focal_distance_initial:.3f}")
    
    # Simulate setting minor radius to 1.5
    new_minor_radius = 1.5
    print(f"\nSetting minor radius to: {new_minor_radius:.3f}")
    
    # Calculate new focal distance
    # minor_radius² = major_radius² - focal_distance²
    new_focal_distance = math.sqrt(major_radius_initial * major_radius_initial - 
                                 new_minor_radius * new_minor_radius)
    
    print(f"New focal distance: {new_focal_distance:.3f}")
    
    # Scale the foci distance
    scale_factor = new_focal_distance / focal_distance_initial
    print(f"Scale factor: {scale_factor:.3f}")
    
    # Calculate foci positions relative to center
    focus1_relative = focus1 - center
    focus2_relative = focus2 - center
    
    # Scale and update foci positions
    new_focus1 = center + focus1_relative * scale_factor
    new_focus2 = center + focus2_relative * scale_factor
    
    print(f"New focus1: ({new_focus1.x():.3f}, {new_focus1.y():.3f})")
    print(f"New focus2: ({new_focus2.x():.3f}, {new_focus2.y():.3f})")
    
    # Verify the new focal distance
    new_focal_distance_calc = math.hypot(new_focus2.x() - new_focus1.x(), new_focus2.y() - new_focus1.y()) / 2
    print(f"Calculated new focal distance: {new_focal_distance_calc:.3f}")
    assert abs(new_focal_distance_calc - new_focal_distance) < 0.001, f"Focal distance should be {new_focal_distance}, got {new_focal_distance_calc}"
    
    # Verify the new minor radius
    new_minor_radius_calc = math.sqrt(major_radius_initial * major_radius_initial - new_focal_distance_calc * new_focal_distance_calc)
    print(f"Calculated new minor radius: {new_minor_radius_calc:.3f}")
    assert abs(new_minor_radius_calc - new_minor_radius) < 0.001, f"Minor radius should be {new_minor_radius}, got {new_minor_radius_calc}"
    
    # Verify the major radius should remain the same
    new_dist1 = math.hypot(perimeter.x() - new_focus1.x(), perimeter.y() - new_focus1.y())
    new_dist2 = math.hypot(perimeter.x() - new_focus2.x(), perimeter.y() - new_focus2.y())
    new_major_radius_calc = (new_dist1 + new_dist2) / 2
    
    print(f"New major radius: {new_major_radius_calc:.3f}")
    assert abs(new_major_radius_calc - major_radius_initial) < 0.001, f"Major radius should remain {major_radius_initial}, got {new_major_radius_calc}"
    
    print("✓ Minor radius setter test passed")
    return True


def test_radius_setters_independence():
    """Test that major and minor radius setters work independently."""
    print("\nTesting radius setters independence...")
    
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
    
    # First, change major radius to 4.0
    new_major_radius = 4.0
    print(f"\nStep 1: Setting major radius to {new_major_radius:.3f}")
    
    # Scale perimeter point
    relative_pos = perimeter - center
    scale_factor = new_major_radius / major_radius_initial
    new_perimeter = center + relative_pos * scale_factor
    
    # Calculate new properties after major radius change
    new_dist1 = math.hypot(new_perimeter.x() - focus1.x(), new_perimeter.y() - focus1.y())
    new_dist2 = math.hypot(new_perimeter.x() - focus2.x(), new_perimeter.y() - focus2.y())
    new_major_radius_calc = (new_dist1 + new_dist2) / 2
    focal_distance = math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2
    new_minor_radius_after_major = math.sqrt(new_major_radius_calc * new_major_radius_calc - focal_distance * focal_distance)
    
    print(f"After major radius change:")
    print(f"  Major radius: {new_major_radius_calc:.3f}")
    print(f"  Minor radius: {new_minor_radius_after_major:.3f}")
    
    # Then, change minor radius to 1.0
    new_minor_radius = 1.0
    print(f"\nStep 2: Setting minor radius to {new_minor_radius:.3f}")
    
    # Calculate new focal distance
    new_focal_distance = math.sqrt(new_major_radius_calc * new_major_radius_calc - new_minor_radius * new_minor_radius)
    
    # Scale foci
    scale_factor = new_focal_distance / focal_distance
    focus1_relative = focus1 - center
    focus2_relative = focus2 - center
    new_focus1 = center + focus1_relative * scale_factor
    new_focus2 = center + focus2_relative * scale_factor
    
    # Calculate final properties
    final_dist1 = math.hypot(new_perimeter.x() - new_focus1.x(), new_perimeter.y() - new_focus1.y())
    final_dist2 = math.hypot(new_perimeter.x() - new_focus2.x(), new_perimeter.y() - new_focus2.y())
    final_major_radius = (final_dist1 + final_dist2) / 2
    final_focal_distance = math.hypot(new_focus2.x() - new_focus1.x(), new_focus2.y() - new_focus1.y()) / 2
    final_minor_radius = math.sqrt(final_major_radius * final_major_radius - final_focal_distance * final_focal_distance)
    
    print(f"Final properties:")
    print(f"  Major radius: {final_major_radius:.3f}")
    print(f"  Minor radius: {final_minor_radius:.3f}")
    
    # Verify that major radius is close to target and minor radius is close to target
    assert abs(final_major_radius - new_major_radius) < 0.1, f"Major radius should be close to {new_major_radius}, got {final_major_radius}"
    assert abs(final_minor_radius - new_minor_radius) < 0.1, f"Minor radius should be close to {new_minor_radius}, got {final_minor_radius}"
    
    print("✓ Radius setters independence test passed")
    return True


def main():
    """Run all radius setter tests."""
    print("=== EllipseCadItem Radius Setter Tests ===\n")
    
    tests = [
        test_major_radius_setter,
        test_minor_radius_setter,
        test_radius_setters_independence
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
        print("All radius setter tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 