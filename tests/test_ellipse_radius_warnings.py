#!/usr/bin/env python3
"""
Test script for EllipseCadItem radius setter warnings.
"""

import math
import sys
import os
import logging
from io import StringIO

# Add the src directory to the path so we can import BelfryCAD modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from BelfryCAD.gui.views.graphics_items.caditems.ellipse_cad_item import EllipseCadItem


class MockMainWindow:
    """Mock main window for testing."""
    def __init__(self):
        self.scene = None


def test_major_radius_warnings():
    """Test that major radius setter warns for invalid values."""
    print("Testing major radius setter warnings...")
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Create a mock main window
    mock_main_window = MockMainWindow()
    
    # Create an ellipse
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    ellipse = EllipseCadItem(
        main_window=mock_main_window,
        focus1_point=focus1,
        focus2_point=focus2,
        perimeter_point=perimeter
    )
    
    print(f"Initial major radius: {ellipse.major_radius:.3f}")
    print(f"Initial minor radius: {ellipse.minor_radius:.3f}")
    
    # Test 1: Negative major radius
    print("\nTesting negative major radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    ellipse._set_major_radius(-1.0)
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert "Major radius must be positive" in log_output, "Should warn about negative major radius"
    assert "got -1.0" in log_output, "Should include the invalid value in warning"
    
    # Test 2: Major radius smaller than minor radius
    print("\nTesting major radius smaller than minor radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    # Set a large minor radius first
    ellipse._set_minor_radius(5.0)
    current_minor = ellipse.minor_radius
    
    # Try to set major radius smaller than minor
    ellipse._set_major_radius(3.0)
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert "Major radius (3.0) cannot be smaller than or equal to minor radius" in log_output, "Should warn about major radius too small"
    
    # Clean up
    logging.getLogger().removeHandler(handler)
    
    print("✓ Major radius warnings test passed")
    return True


def test_minor_radius_warnings():
    """Test that minor radius setter warns for invalid values."""
    print("\nTesting minor radius setter warnings...")
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Create a mock main window
    mock_main_window = MockMainWindow()
    
    # Create an ellipse
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    ellipse = EllipseCadItem(
        main_window=mock_main_window,
        focus1_point=focus1,
        focus2_point=focus2,
        perimeter_point=perimeter
    )
    
    print(f"Initial major radius: {ellipse.major_radius:.3f}")
    print(f"Initial minor radius: {ellipse.minor_radius:.3f}")
    
    # Test 1: Negative minor radius
    print("\nTesting negative minor radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    ellipse._set_minor_radius(-1.0)
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert "Minor radius must be positive" in log_output, "Should warn about negative minor radius"
    assert "got -1.0" in log_output, "Should include the invalid value in warning"
    
    # Test 2: Minor radius larger than major radius
    print("\nTesting minor radius larger than major radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    # Try to set minor radius larger than major
    ellipse._set_minor_radius(5.0)
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert "Minor radius (5.0) cannot be larger than or equal to major radius" in log_output, "Should warn about minor radius too large"
    
    # Clean up
    logging.getLogger().removeHandler(handler)
    
    print("✓ Minor radius warnings test passed")
    return True


def test_valid_radius_changes():
    """Test that valid radius changes don't produce warnings."""
    print("\nTesting valid radius changes...")
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Create a mock main window
    mock_main_window = MockMainWindow()
    
    # Create an ellipse
    focus1 = QPointF(-2, 0)
    focus2 = QPointF(2, 0)
    perimeter = QPointF(3, 0)
    
    ellipse = EllipseCadItem(
        main_window=mock_main_window,
        focus1_point=focus1,
        focus2_point=focus2,
        perimeter_point=perimeter
    )
    
    print(f"Initial major radius: {ellipse.major_radius:.3f}")
    print(f"Initial minor radius: {ellipse.minor_radius:.3f}")
    
    # Test valid major radius change
    print("\nTesting valid major radius change...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    ellipse._set_major_radius(5.0)
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert log_output.strip() == "", "Should not produce warnings for valid major radius change"
    
    # Test valid minor radius change
    print("\nTesting valid minor radius change...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    ellipse._set_minor_radius(2.0)
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert log_output.strip() == "", "Should not produce warnings for valid minor radius change"
    
    # Clean up
    logging.getLogger().removeHandler(handler)
    
    print("✓ Valid radius changes test passed")
    return True


def main():
    """Run all ellipse radius warning tests."""
    print("=== EllipseCadItem Radius Warning Tests ===\n")
    
    tests = [
        test_major_radius_warnings,
        test_minor_radius_warnings,
        test_valid_radius_changes
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
        print("All ellipse radius warning tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 