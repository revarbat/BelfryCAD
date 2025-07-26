#!/usr/bin/env python3
"""
Test script for EllipseCadItem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from BelfryCAD.gui.views.graphics_items.caditems.ellipse_cad_item import EllipseCadItem


def test_ellipse_cad_item_basic():
    """Test basic ellipse CAD item functionality."""
    print("Testing basic EllipseCadItem functionality...")
    
    # Create QApplication for Qt widgets
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create a mock main window (simplified for testing)
    class MockMainWindow:
        def __init__(self):
            self.cad_scene = None
    
    main_window = MockMainWindow()
    
    # Create ellipse with default points
    ellipse = EllipseCadItem(main_window)
    
    # Test basic properties
    print(f"Focus 1: ({ellipse.focus1_point.x():.3f}, {ellipse.focus1_point.y():.3f})")
    print(f"Focus 2: ({ellipse.focus2_point.x():.3f}, {ellipse.focus2_point.y():.3f})")
    print(f"Perimeter: ({ellipse.perimeter_point.x():.3f}, {ellipse.perimeter_point.y():.3f})")
    print(f"Center: ({ellipse.center_point.x():.3f}, {ellipse.center_point.y():.3f})")
    print(f"Major radius: {ellipse.major_radius:.3f}")
    print(f"Minor radius: {ellipse.minor_radius:.3f}")
    print(f"Rotation angle: {ellipse.rotation_angle:.3f}")
    print(f"Eccentricity: {ellipse.eccentricity:.3f}")
    
    # Test bounding rect
    bbox = ellipse.boundingRect()
    print(f"Bounding box: ({bbox.x():.3f}, {bbox.y():.3f}, {bbox.width():.3f}, {bbox.height():.3f})")
    
    return True


def test_ellipse_cad_item_custom_points():
    """Test ellipse CAD item with custom points."""
    print("\nTesting EllipseCadItem with custom points...")
    
    # Create QApplication for Qt widgets
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create a mock main window
    class MockMainWindow:
        def __init__(self):
            self.cad_scene = None
    
    main_window = MockMainWindow()
    
    # Create ellipse with custom points
    focus1 = QPointF(-3, 0)
    focus2 = QPointF(3, 0)
    perimeter = QPointF(4, 0)
    
    ellipse = EllipseCadItem(main_window, focus1, focus2, perimeter)
    
    # Test properties
    print(f"Focus 1: ({ellipse.focus1_point.x():.3f}, {ellipse.focus1_point.y():.3f})")
    print(f"Focus 2: ({ellipse.focus2_point.x():.3f}, {ellipse.focus2_point.y():.3f})")
    print(f"Perimeter: ({ellipse.perimeter_point.x():.3f}, {ellipse.perimeter_point.y():.3f})")
    print(f"Center: ({ellipse.center_point.x():.3f}, {ellipse.center_point.y():.3f})")
    print(f"Major radius: {ellipse.major_radius:.3f}")
    print(f"Minor radius: {ellipse.minor_radius:.3f}")
    print(f"Rotation angle: {ellipse.rotation_angle:.3f}")
    print(f"Eccentricity: {ellipse.eccentricity:.3f}")
    
    return True


def test_ellipse_cad_item_control_points():
    """Test ellipse CAD item control points."""
    print("\nTesting EllipseCadItem control points...")
    
    # Create QApplication for Qt widgets
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create a mock main window
    class MockMainWindow:
        def __init__(self):
            self.cad_scene = None
    
    main_window = MockMainWindow()
    
    # Create ellipse
    ellipse = EllipseCadItem(main_window)
    
    # Test control points creation
    control_points = ellipse._create_controls_impl()
    print(f"Created {len(control_points)} control points")
    
    # Test control point positions
    cp_positions = ellipse.getControlPoints()
    print(f"Control point positions: {len(cp_positions)}")
    for i, pos in enumerate(cp_positions):
        print(f"  CP {i}: ({pos.x():.3f}, {pos.y():.3f})")
    
    # Test control point objects
    cp_objects = ellipse._get_control_point_objects()
    print(f"Control point objects: {len(cp_objects)}")
    
    return True


def test_ellipse_cad_item_setters():
    """Test ellipse CAD item setters."""
    print("\nTesting EllipseCadItem setters...")
    
    # Create QApplication for Qt widgets
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create a mock main window
    class MockMainWindow:
        def __init__(self):
            self.cad_scene = None
    
    main_window = MockMainWindow()
    
    # Create ellipse
    ellipse = EllipseCadItem(main_window)
    
    # Test focus position setters
    new_focus1 = QPointF(-4, 0)
    ellipse._set_focus1_position(new_focus1)
    print(f"New focus 1: ({ellipse.focus1_point.x():.3f}, {ellipse.focus1_point.y():.3f})")
    
    new_focus2 = QPointF(4, 0)
    ellipse._set_focus2_position(new_focus2)
    print(f"New focus 2: ({ellipse.focus2_point.x():.3f}, {ellipse.focus2_point.y():.3f})")
    
    new_perimeter = QPointF(5, 0)
    ellipse._set_perimeter_position(new_perimeter)
    print(f"New perimeter: ({ellipse.perimeter_point.x():.3f}, {ellipse.perimeter_point.y():.3f})")
    
    # Test datum setters
    ellipse._set_major_radius(6.0)
    print(f"New major radius: {ellipse.major_radius:.3f}")
    
    ellipse._set_minor_radius(4.0)
    print(f"New minor radius: {ellipse.minor_radius:.3f}")
    
    ellipse._set_rotation_angle(45.0)
    print(f"New rotation angle: {ellipse.rotation_angle:.3f}")
    
    return True


def main():
    """Run all ellipse CAD item tests."""
    print("=== EllipseCadItem Tests ===\n")
    
    tests = [
        test_ellipse_cad_item_basic,
        test_ellipse_cad_item_custom_points,
        test_ellipse_cad_item_control_points,
        test_ellipse_cad_item_setters
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
        print("All EllipseCadItem tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 