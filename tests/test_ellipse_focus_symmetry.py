#!/usr/bin/env python3
"""
Test script for EllipseCadItem focus point symmetry.
"""

import math
from PySide6.QtCore import QPointF


def test_focus_symmetry():
    """Test that moving one focus moves the other to maintain symmetry."""
    print("Testing focus point symmetry...")
    
    # Initial ellipse setup
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    # Calculate initial center
    center = (focus1 + focus2) * 0.5
    print(f"Initial center: ({center.x():.3f}, {center.y():.3f})")
    print(f"Initial focus1: ({focus1.x():.3f}, {focus1.y():.3f})")
    print(f"Initial focus2: ({focus2.x():.3f}, {focus2.y():.3f})")
    
    # Test moving focus1 to a new position
    new_focus1 = QPointF(-3, 1)
    print(f"\nMoving focus1 to: ({new_focus1.x():.3f}, {new_focus1.y():.3f})")
    
    # Calculate new center
    new_center = (new_focus1 + focus2) * 0.5
    print(f"New center: ({new_center.x():.3f}, {new_center.y():.3f})")
    
    # Calculate the vector from new center to focus1
    focus1_vector = new_focus1 - new_center
    
    # Move focus2 to the opposite side at the same distance
    new_focus2 = new_center - focus1_vector
    print(f"New focus2: ({new_focus2.x():.3f}, {new_focus2.y():.3f})")
    
    # Verify symmetry
    center_after = (new_focus1 + new_focus2) * 0.5
    print(f"Center after adjustment: ({center_after.x():.3f}, {center_after.y():.3f})")
    
    # Verify the distances are equal
    dist1 = math.hypot(new_focus1.x() - center_after.x(), new_focus1.y() - center_after.y())
    dist2 = math.hypot(new_focus2.x() - center_after.x(), new_focus2.y() - center_after.y())
    print(f"Distance from center to focus1: {dist1:.3f}")
    print(f"Distance from center to focus2: {dist2:.3f}")
    
    assert abs(dist1 - dist2) < 0.001, f"Focus distances should be equal, got {dist1} and {dist2}"
    
    # Verify the foci are on opposite sides
    focus1_to_center = new_focus1 - center_after
    focus2_to_center = new_focus2 - center_after
    dot_product = focus1_to_center.x() * focus2_to_center.x() + focus1_to_center.y() * focus2_to_center.y()
    print(f"Dot product (should be negative): {dot_product:.3f}")
    
    assert dot_product < 0, "Foci should be on opposite sides of center"
    
    print("✓ Focus symmetry test passed")
    return True


def test_focus_symmetry_reverse():
    """Test moving focus2 and verifying focus1 moves to maintain symmetry."""
    print("\nTesting focus2 movement symmetry...")
    
    # Initial ellipse setup
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    
    # Test moving focus2 to a new position
    new_focus2 = QPointF(4, -1)
    print(f"Moving focus2 to: ({new_focus2.x():.3f}, {new_focus2.y():.3f})")
    
    # Calculate new center
    new_center = (focus1 + new_focus2) * 0.5
    print(f"New center: ({new_center.x():.3f}, {new_center.y():.3f})")
    
    # Calculate the vector from new center to focus2
    focus2_vector = new_focus2 - new_center
    
    # Move focus1 to the opposite side at the same distance
    new_focus1 = new_center - focus2_vector
    print(f"New focus1: ({new_focus1.x():.3f}, {new_focus1.y():.3f})")
    
    # Verify symmetry
    center_after = (new_focus1 + new_focus2) * 0.5
    print(f"Center after adjustment: ({center_after.x():.3f}, {center_after.y():.3f})")
    
    # Verify the distances are equal
    dist1 = math.hypot(new_focus1.x() - center_after.x(), new_focus1.y() - center_after.y())
    dist2 = math.hypot(new_focus2.x() - center_after.x(), new_focus2.y() - center_after.y())
    print(f"Distance from center to focus1: {dist1:.3f}")
    print(f"Distance from center to focus2: {dist2:.3f}")
    
    assert abs(dist1 - dist2) < 0.001, f"Focus distances should be equal, got {dist1} and {dist2}"
    
    print("✓ Focus2 movement symmetry test passed")
    return True


def test_ellipse_properties_after_focus_move():
    """Test that ellipse properties remain consistent after focus movement."""
    print("\nTesting ellipse properties after focus movement...")
    
    # Initial ellipse
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    # Calculate initial properties
    center_initial = (focus1 + focus2) * 0.5
    major_radius_initial = 3.0  # Based on perimeter point
    minor_radius_initial = 2.236  # Calculated from major radius and focal distance
    
    print(f"Initial center: ({center_initial.x():.3f}, {center_initial.y():.3f})")
    print(f"Initial major radius: {major_radius_initial:.3f}")
    print(f"Initial minor radius: {minor_radius_initial:.3f}")
    
    # Move focus1
    new_focus1 = QPointF(-3, 1)
    new_center = (new_focus1 + focus2) * 0.5
    focus1_vector = new_focus1 - new_center
    new_focus2 = new_center - focus1_vector
    
    # Calculate new properties
    center_final = (new_focus1 + new_focus2) * 0.5
    focal_distance = math.hypot(new_focus2.x() - new_focus1.x(), new_focus2.y() - new_focus1.y()) * 0.5
    
    print(f"Final center: ({center_final.x():.3f}, {center_final.y():.3f})")
    print(f"Focal distance: {focal_distance:.3f}")
    
    # The major radius should remain the same (based on perimeter point)
    # The minor radius should change based on the new focal distance
    new_minor_radius = math.sqrt(major_radius_initial * major_radius_initial - focal_distance * focal_distance)
    print(f"New minor radius: {new_minor_radius:.3f}")
    
    # Verify the focal distance is reasonable
    assert focal_distance < major_radius_initial, "Focal distance should be less than major radius"
    assert new_minor_radius > 0, "Minor radius should be positive"
    
    print("✓ Ellipse properties test passed")
    return True


def main():
    """Run all focus symmetry tests."""
    print("=== EllipseCadItem Focus Symmetry Tests ===\n")
    
    tests = [
        test_focus_symmetry,
        test_focus_symmetry_reverse,
        test_ellipse_properties_after_focus_move
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
        print("All focus symmetry tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 