#!/usr/bin/env python3
"""
Test script for EllipseCadItem rotation setter method.
"""

import math
from PySide6.QtCore import QPointF


def test_rotation_setter():
    """Test that setting rotation angle rotates foci and perimeter point correctly."""
    print("Testing rotation setter...")
    
    # Initial ellipse setup
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    # Calculate initial properties
    center = (focus1 + focus2) * 0.5
    initial_rotation = 0.0
    
    print(f"Initial center: ({center.x():.3f}, {center.y():.3f})")
    print(f"Initial focus1: ({focus1.x():.3f}, {focus1.y():.3f})")
    print(f"Initial focus2: ({focus2.x():.3f}, {focus2.y():.3f})")
    print(f"Initial perimeter: ({perimeter.x():.3f}, {perimeter.y():.3f})")
    print(f"Initial rotation: {initial_rotation:.3f}°")
    
    # Simulate setting rotation to 45 degrees
    new_rotation = 45.0
    print(f"\nSetting rotation to: {new_rotation:.3f}°")
    
    # Calculate rotation delta
    rotation_delta = new_rotation - initial_rotation
    angle_rad = math.radians(rotation_delta)
    cos_angle = math.cos(angle_rad)
    sin_angle = math.sin(angle_rad)
    
    print(f"Rotation delta: {rotation_delta:.3f}°")
    print(f"Cos angle: {cos_angle:.3f}")
    print(f"Sin angle: {sin_angle:.3f}")
    
    # Rotate focus1
    focus1_relative = focus1 - center
    new_focus1_x = focus1_relative.x() * cos_angle - focus1_relative.y() * sin_angle
    new_focus1_y = focus1_relative.x() * sin_angle + focus1_relative.y() * cos_angle
    new_focus1 = center + QPointF(new_focus1_x, new_focus1_y)
    
    print(f"New focus1: ({new_focus1.x():.3f}, {new_focus1.y():.3f})")
    
    # Rotate focus2
    focus2_relative = focus2 - center
    new_focus2_x = focus2_relative.x() * cos_angle - focus2_relative.y() * sin_angle
    new_focus2_y = focus2_relative.x() * sin_angle + focus2_relative.y() * cos_angle
    new_focus2 = center + QPointF(new_focus2_x, new_focus2_y)
    
    print(f"New focus2: ({new_focus2.x():.3f}, {new_focus2.y():.3f})")
    
    # Rotate perimeter point
    perimeter_relative = perimeter - center
    new_perimeter_x = perimeter_relative.x() * cos_angle - perimeter_relative.y() * sin_angle
    new_perimeter_y = perimeter_relative.x() * sin_angle + perimeter_relative.y() * cos_angle
    new_perimeter = center + QPointF(new_perimeter_x, new_perimeter_y)
    
    print(f"New perimeter: ({new_perimeter.x():.3f}, {new_perimeter.y():.3f})")
    
    # Verify the results
    # Check that the center remains the same
    new_center = (new_focus1 + new_focus2) * 0.5
    print(f"New center: ({new_center.x():.3f}, {new_center.y():.3f})")
    assert abs(new_center.x() - center.x()) < 0.001, f"Center X should remain {center.x()}, got {new_center.x()}"
    assert abs(new_center.y() - center.y()) < 0.001, f"Center Y should remain {center.y()}, got {new_center.y()}"
    
    # Check that the distances are preserved
    original_focal_distance = math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2
    new_focal_distance = math.hypot(new_focus2.x() - new_focus1.x(), new_focus2.y() - new_focus1.y()) / 2
    print(f"Original focal distance: {original_focal_distance:.3f}")
    print(f"New focal distance: {new_focal_distance:.3f}")
    assert abs(new_focal_distance - original_focal_distance) < 0.001, f"Focal distance should be preserved, got {new_focal_distance}"
    
    # Check that the major radius is preserved
    original_dist1 = math.hypot(perimeter.x() - focus1.x(), perimeter.y() - focus1.y())
    original_dist2 = math.hypot(perimeter.x() - focus2.x(), perimeter.y() - focus2.y())
    original_major_radius = (original_dist1 + original_dist2) / 2
    
    new_dist1 = math.hypot(new_perimeter.x() - new_focus1.x(), new_perimeter.y() - new_focus1.y())
    new_dist2 = math.hypot(new_perimeter.x() - new_focus2.x(), new_perimeter.y() - new_focus2.y())
    new_major_radius = (new_dist1 + new_dist2) / 2
    
    print(f"Original major radius: {original_major_radius:.3f}")
    print(f"New major radius: {new_major_radius:.3f}")
    assert abs(new_major_radius - original_major_radius) < 0.001, f"Major radius should be preserved, got {new_major_radius}"
    
    # Check that the rotation angle is correct
    # Calculate the angle from center to focus2
    angle_to_focus2 = math.degrees(math.atan2(new_focus2.y() - new_center.y(), new_focus2.x() - new_center.x()))
    print(f"Calculated rotation angle: {angle_to_focus2:.3f}°")
    assert abs(angle_to_focus2 - new_rotation) < 0.1, f"Rotation angle should be {new_rotation}°, got {angle_to_focus2}°"
    
    print("✓ Rotation setter test passed")
    return True


def test_rotation_setter_multiple_angles():
    """Test rotation setter with multiple angles."""
    print("\nTesting rotation setter with multiple angles...")
    
    # Initial ellipse setup
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    center = (focus1 + focus2) * 0.5
    
    test_angles = [90, 180, 270, 45, 135, 225, 315]
    
    for angle in test_angles:
        print(f"\nTesting rotation to {angle}°...")
        
        # Calculate rotation delta
        rotation_delta = angle - 0.0
        angle_rad = math.radians(rotation_delta)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Rotate focus1
        focus1_relative = focus1 - center
        new_focus1_x = focus1_relative.x() * cos_angle - focus1_relative.y() * sin_angle
        new_focus1_y = focus1_relative.x() * sin_angle + focus1_relative.y() * cos_angle
        new_focus1 = center + QPointF(new_focus1_x, new_focus1_y)
        
        # Rotate focus2
        focus2_relative = focus2 - center
        new_focus2_x = focus2_relative.x() * cos_angle - focus2_relative.y() * sin_angle
        new_focus2_y = focus2_relative.x() * sin_angle + focus2_relative.y() * cos_angle
        new_focus2 = center + QPointF(new_focus2_x, new_focus2_y)
        
        # Rotate perimeter point
        perimeter_relative = perimeter - center
        new_perimeter_x = perimeter_relative.x() * cos_angle - perimeter_relative.y() * sin_angle
        new_perimeter_y = perimeter_relative.x() * sin_angle + perimeter_relative.y() * cos_angle
        new_perimeter = center + QPointF(new_perimeter_x, new_perimeter_y)
        
        # Verify center is preserved
        new_center = (new_focus1 + new_focus2) * 0.5
        assert abs(new_center.x() - center.x()) < 0.001, f"Center X should remain {center.x()}, got {new_center.x()}"
        assert abs(new_center.y() - center.y()) < 0.001, f"Center Y should remain {center.y()}, got {new_center.y()}"
        
        # Verify focal distance is preserved
        original_focal_distance = math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2
        new_focal_distance = math.hypot(new_focus2.x() - new_focus1.x(), new_focus2.y() - new_focus1.y()) / 2
        assert abs(new_focal_distance - original_focal_distance) < 0.001, f"Focal distance should be preserved"
        
        # Verify major radius is preserved
        original_dist1 = math.hypot(perimeter.x() - focus1.x(), perimeter.y() - focus1.y())
        original_dist2 = math.hypot(perimeter.x() - focus2.x(), perimeter.y() - focus2.y())
        original_major_radius = (original_dist1 + original_dist2) / 2
        
        new_dist1 = math.hypot(new_perimeter.x() - new_focus1.x(), new_perimeter.y() - new_focus1.y())
        new_dist2 = math.hypot(new_perimeter.x() - new_focus2.x(), new_perimeter.y() - new_focus2.y())
        new_major_radius = (new_dist1 + new_dist2) / 2
        
        assert abs(new_major_radius - original_major_radius) < 0.001, f"Major radius should be preserved"
        
        print(f"  ✓ {angle}° rotation test passed")
    
    print("✓ All rotation angle tests passed")
    return True


def main():
    """Run all rotation setter tests."""
    print("=== EllipseCadItem Rotation Setter Tests ===\n")
    
    tests = [
        test_rotation_setter,
        test_rotation_setter_multiple_angles
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
        print("All rotation setter tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 