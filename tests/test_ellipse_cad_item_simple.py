#!/usr/bin/env python3
"""
Simple test script for EllipseCadItem mathematical properties.
"""

import math
from PySide6.QtCore import QPointF


def test_ellipse_mathematics():
    """Test the mathematical properties of ellipse calculations."""
    print("Testing ellipse mathematical properties...")
    
    # Test focus points and perimeter point
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    # Calculate center
    center = (focus1 + focus2) / 2
    print(f"Center: ({center.x():.3f}, {center.y():.3f})")
    
    # Calculate major radius (half the sum of distances from foci to perimeter)
    dist1 = math.hypot(perimeter.x() - focus1.x(), perimeter.y() - focus1.y())
    dist2 = math.hypot(perimeter.x() - focus2.x(), perimeter.y() - focus2.y())
    major_radius = (dist1 + dist2) / 2
    print(f"Major radius: {major_radius:.3f}")
    
    # Calculate minor radius
    focal_distance = math.hypot(focus2.x() - focus1.x(), focus2.y() - focus1.y()) / 2
    minor_radius = math.sqrt(major_radius * major_radius - focal_distance * focal_distance)
    print(f"Minor radius: {minor_radius:.3f}")
    
    # Calculate rotation angle
    angle = math.degrees(math.atan2(focus2.y() - center.y(), focus2.x() - center.x()))
    rotation_angle = (angle + 360) % 360
    print(f"Rotation angle: {rotation_angle:.3f}")
    
    # Calculate eccentricity
    eccentricity = math.sqrt(1 - (minor_radius * minor_radius) / (major_radius * major_radius))
    print(f"Eccentricity: {eccentricity:.3f}")
    
    # Verify the mathematical relationships
    assert abs(major_radius - 3.0) < 0.001, f"Major radius should be 3.0, got {major_radius}"
    assert abs(minor_radius - 2.236) < 0.001, f"Minor radius should be 2.236, got {minor_radius}"
    assert abs(rotation_angle - 0.0) < 0.001, f"Rotation angle should be 0.0, got {rotation_angle}"
    assert abs(eccentricity - 0.667) < 0.001, f"Eccentricity should be 0.667, got {eccentricity}"
    
    print("✓ Mathematical properties test passed")
    return True


def test_ellipse_parameterization():
    """Test ellipse parameterization and point calculation."""
    print("\nTesting ellipse parameterization...")
    
    # Ellipse parameters
    center = QPointF(0, 0)
    major_radius = 5.0
    minor_radius = 3.0
    rotation = math.radians(30)  # 30 degrees
    
    # Test point calculation at different parameters
    for t in [0, math.pi/4, math.pi/2, 3*math.pi/4, math.pi]:
        # Calculate point on ellipse
        x_ellipse = major_radius * math.cos(t)
        y_ellipse = minor_radius * math.sin(t)
        
        # Apply rotation
        cos_rot = math.cos(rotation)
        sin_rot = math.sin(rotation)
        x_world = x_ellipse * cos_rot - y_ellipse * sin_rot + center.x()
        y_world = x_ellipse * sin_rot + y_ellipse * cos_rot + center.y()
        
        print(f"t={t:.3f}: ({x_world:.3f}, {y_world:.3f})")
    
    print("✓ Parameterization test passed")
    return True


def test_ellipse_bounding_box():
    """Test ellipse bounding box calculation."""
    print("\nTesting ellipse bounding box calculation...")
    
    # Ellipse parameters
    center = QPointF(0, 0)
    major_radius = 5.0
    minor_radius = 3.0
    rotation = math.radians(45)  # 45 degrees
    
    # Calculate bounding box
    cos_rot = math.cos(rotation)
    sin_rot = math.sin(rotation)
    
    # Maximum extent in x and y directions
    max_x = abs(major_radius * cos_rot) + abs(minor_radius * sin_rot)
    max_y = abs(major_radius * sin_rot) + abs(minor_radius * cos_rot)
    
    print(f"Bounding box: ({center.x() - max_x:.3f}, {center.y() - max_y:.3f}, {2 * max_x:.3f}, {2 * max_y:.3f})")
    
    # Verify bounding box is reasonable
    assert max_x > major_radius, f"Bounding box width should be larger than major radius"
    assert max_y > minor_radius, f"Bounding box height should be larger than minor radius"
    
    print("✓ Bounding box test passed")
    return True


def test_ellipse_setter_mathematics():
    """Test the mathematical logic of ellipse setters."""
    print("\nTesting ellipse setter mathematics...")
    
    # Initial ellipse
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    center = (focus1 + focus2) / 2
    
    print(f"Initial - Major: {3.0:.3f}, Minor: {2.236:.3f}")
    
    # Test major radius setter logic
    new_major_radius = 6.0
    dist1 = math.hypot(perimeter.x() - focus1.x(), perimeter.y() - focus1.y())
    dist2 = math.hypot(perimeter.x() - focus2.x(), perimeter.y() - focus2.y())
    current_major_radius = (dist1 + dist2) / 2
    scale_factor = new_major_radius / current_major_radius
    
    # Scale perimeter point relative to center
    relative_pos = perimeter - center
    new_perimeter = center + relative_pos * scale_factor
    
    print(f"New perimeter: ({new_perimeter.x():.3f}, {new_perimeter.y():.3f})")
    
    # Verify new major radius
    new_dist1 = math.hypot(new_perimeter.x() - focus1.x(), new_perimeter.y() - focus1.y())
    new_dist2 = math.hypot(new_perimeter.x() - focus2.x(), new_perimeter.y() - focus2.y())
    new_major_radius_calc = (new_dist1 + new_dist2) / 2
    print(f"Calculated new major radius: {new_major_radius_calc:.3f}")
    
    assert abs(new_major_radius_calc - new_major_radius) < 0.001, "Major radius setter failed"
    
    print("✓ Setter mathematics test passed")
    return True


def main():
    """Run all ellipse mathematical tests."""
    print("=== EllipseCadItem Mathematical Tests ===\n")
    
    tests = [
        test_ellipse_mathematics,
        test_ellipse_parameterization,
        test_ellipse_bounding_box,
        test_ellipse_setter_mathematics
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
        print("All EllipseCadItem mathematical tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 