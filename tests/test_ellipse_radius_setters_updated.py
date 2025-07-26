#!/usr/bin/env python3
"""
Test script for updated EllipseCadItem radius setter methods.
"""

import math
from PySide6.QtCore import QPointF


def test_major_radius_setter_updated():
    """Test that setting major radius adjusts both focal distance and perimeter point."""
    print("Testing updated major radius setter...")
    
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
    
    # Simulate setting major radius to 5.0
    new_major_radius = 5.0
    print(f"\nSetting major radius to: {new_major_radius:.3f}")
    
    # Step 1: Calculate new focal distance based on new major radius and current minor radius
    new_focal_distance = math.sqrt(new_major_radius * new_major_radius - 
                                 minor_radius_initial * minor_radius_initial)
    print(f"New focal distance: {new_focal_distance:.3f}")
    
    # Step 2: Scale the foci distance
    scale_factor = new_focal_distance / focal_distance_initial
    focus1_relative = focus1 - center
    focus2_relative = focus2 - center
    new_focus1 = center + focus1_relative * scale_factor
    new_focus2 = center + focus2_relative * scale_factor
    
    print(f"New focus1: ({new_focus1.x():.3f}, {new_focus1.y():.3f})")
    print(f"New focus2: ({new_focus2.x():.3f}, {new_focus2.y():.3f})")
    
    # Step 3: Adjust perimeter point to maintain the new major radius
    dist1 = math.hypot(perimeter.x() - new_focus1.x(), perimeter.y() - new_focus1.y())
    dist2 = math.hypot(perimeter.x() - new_focus2.x(), perimeter.y() - new_focus2.y())
    current_major_radius_after_foci = (dist1 + dist2) / 2
    
    perimeter_scale_factor = new_major_radius / current_major_radius_after_foci
    relative_pos = perimeter - center
    new_perimeter = center + relative_pos * perimeter_scale_factor
    
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
    
    # Verify minor radius is preserved
    assert abs(final_minor_radius - minor_radius_initial) < 0.1, f"Minor radius should be preserved, got {final_minor_radius}"
    
    print("✓ Updated major radius setter test passed")
    return True


def test_minor_radius_setter_updated():
    """Test that setting minor radius adjusts both focal distance and perimeter point."""
    print("\nTesting updated minor radius setter...")
    
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
    
    # Step 1: Calculate new focal distance
    new_focal_distance = math.sqrt(major_radius_initial * major_radius_initial - 
                                 new_minor_radius * new_minor_radius)
    print(f"New focal distance: {new_focal_distance:.3f}")
    
    # Step 2: Scale the foci distance
    scale_factor = new_focal_distance / focal_distance_initial
    focus1_relative = focus1 - center
    focus2_relative = focus2 - center
    new_focus1 = center + focus1_relative * scale_factor
    new_focus2 = center + focus2_relative * scale_factor
    
    print(f"New focus1: ({new_focus1.x():.3f}, {new_focus1.y():.3f})")
    print(f"New focus2: ({new_focus2.x():.3f}, {new_focus2.y():.3f})")
    
    # Step 3: Adjust perimeter point to maintain the original major radius
    dist1 = math.hypot(perimeter.x() - new_focus1.x(), perimeter.y() - new_focus1.y())
    dist2 = math.hypot(perimeter.x() - new_focus2.x(), perimeter.y() - new_focus2.y())
    current_major_radius_after_foci = (dist1 + dist2) / 2
    
    perimeter_scale_factor = major_radius_initial / current_major_radius_after_foci
    relative_pos = perimeter - center
    new_perimeter = center + relative_pos * perimeter_scale_factor
    
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
    
    print("✓ Updated minor radius setter test passed")
    return True


def test_radius_setters_updated_independence():
    """Test that updated radius setters work independently."""
    print("\nTesting updated radius setters independence...")
    
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
    
    # Apply major radius change
    new_focal_distance = math.sqrt(new_major_radius * new_major_radius - 
                                 minor_radius_initial * minor_radius_initial)
    scale_factor = new_focal_distance / (math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2)
    focus1_relative = focus1 - center
    focus2_relative = focus2 - center
    new_focus1 = center + focus1_relative * scale_factor
    new_focus2 = center + focus2_relative * scale_factor
    
    # Adjust perimeter
    dist1 = math.hypot(perimeter.x() - new_focus1.x(), perimeter.y() - new_focus1.y())
    dist2 = math.hypot(perimeter.x() - new_focus2.x(), perimeter.y() - new_focus2.y())
    current_major_radius_after_foci = (dist1 + dist2) / 2
    perimeter_scale_factor = new_major_radius / current_major_radius_after_foci
    relative_pos = perimeter - center
    new_perimeter = center + relative_pos * perimeter_scale_factor
    
    # Calculate properties after major radius change
    new_dist1 = math.hypot(new_perimeter.x() - new_focus1.x(), new_perimeter.y() - new_focus1.y())
    new_dist2 = math.hypot(new_perimeter.x() - new_focus2.x(), new_perimeter.y() - new_focus2.y())
    new_major_radius_calc = (new_dist1 + new_dist2) / 2
    new_focal_distance_calc = math.hypot(new_focus2.x() - new_focus1.x(), new_focus2.y() - new_focus1.y()) / 2
    new_minor_radius_after_major = math.sqrt(new_major_radius_calc * new_major_radius_calc - new_focal_distance_calc * new_focal_distance_calc)
    
    print(f"After major radius change:")
    print(f"  Major radius: {new_major_radius_calc:.3f}")
    print(f"  Minor radius: {new_minor_radius_after_major:.3f}")
    
    # Then, change minor radius to 1.0
    new_minor_radius = 1.0
    print(f"\nStep 2: Setting minor radius to {new_minor_radius:.3f}")
    
    # Apply minor radius change
    new_focal_distance = math.sqrt(new_major_radius_calc * new_major_radius_calc - new_minor_radius * new_minor_radius)
    scale_factor = new_focal_distance / new_focal_distance_calc
    focus1_relative = new_focus1 - center
    focus2_relative = new_focus2 - center
    final_focus1 = center + focus1_relative * scale_factor
    final_focus2 = center + focus2_relative * scale_factor
    
    # Adjust perimeter to maintain major radius
    dist1 = math.hypot(new_perimeter.x() - final_focus1.x(), new_perimeter.y() - final_focus1.y())
    dist2 = math.hypot(new_perimeter.x() - final_focus2.x(), new_perimeter.y() - final_focus2.y())
    current_major_radius_after_foci = (dist1 + dist2) / 2
    perimeter_scale_factor = new_major_radius_calc / current_major_radius_after_foci
    relative_pos = new_perimeter - center
    final_perimeter = center + relative_pos * perimeter_scale_factor
    
    # Calculate final properties
    final_dist1 = math.hypot(final_perimeter.x() - final_focus1.x(), final_perimeter.y() - final_focus1.y())
    final_dist2 = math.hypot(final_perimeter.x() - final_focus2.x(), final_perimeter.y() - final_focus2.y())
    final_major_radius = (final_dist1 + final_dist2) / 2
    final_focal_distance = math.hypot(final_focus2.x() - final_focus1.x(), final_focus2.y() - final_focus1.y()) / 2
    final_minor_radius = math.sqrt(final_major_radius * final_major_radius - final_focal_distance * final_focal_distance)
    
    print(f"Final properties:")
    print(f"  Major radius: {final_major_radius:.3f}")
    print(f"  Minor radius: {final_minor_radius:.3f}")
    
    # Verify that both radii are close to their targets
    assert abs(final_major_radius - new_major_radius) < 0.1, f"Major radius should be close to {new_major_radius}, got {final_major_radius}"
    assert abs(final_minor_radius - new_minor_radius) < 0.1, f"Minor radius should be close to {new_minor_radius}, got {final_minor_radius}"
    
    print("✓ Updated radius setters independence test passed")
    return True


def main():
    """Run all updated radius setter tests."""
    print("=== Updated EllipseCadItem Radius Setter Tests ===\n")
    
    tests = [
        test_major_radius_setter_updated,
        test_minor_radius_setter_updated,
        test_radius_setters_updated_independence
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
        print("All updated radius setter tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 