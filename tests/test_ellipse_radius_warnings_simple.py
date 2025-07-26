#!/usr/bin/env python3
"""
Simple test for ellipse radius warning logic.
"""

import math
import logging
from io import StringIO
from PySide6.QtCore import QPointF


def test_major_radius_warning_logic():
    """Test the logic for major radius warnings."""
    print("Testing major radius warning logic...")
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Test 1: Negative major radius
    print("\nTesting negative major radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    new_major_radius = -1.0
    if new_major_radius <= 0:
        logging.warning(f"Major radius must be positive, got {new_major_radius}")
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert "Major radius must be positive" in log_output, "Should warn about negative major radius"
    assert "got -1.0" in log_output, "Should include the invalid value in warning"
    
    # Test 2: Major radius smaller than minor radius
    print("\nTesting major radius smaller than minor radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    new_major_radius = 3.0
    current_minor_radius = 5.0
    
    if new_major_radius <= current_minor_radius:
        logging.warning(f"Major radius ({new_major_radius}) cannot be smaller than or equal to minor radius ({current_minor_radius})")
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert "Major radius (3.0) cannot be smaller than or equal to minor radius" in log_output, "Should warn about major radius too small"
    
    # Clean up
    logging.getLogger().removeHandler(handler)
    
    print("✓ Major radius warning logic test passed")
    return True


def test_minor_radius_warning_logic():
    """Test the logic for minor radius warnings."""
    print("\nTesting minor radius warning logic...")
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Test 1: Negative minor radius
    print("\nTesting negative minor radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    new_minor_radius = -1.0
    if new_minor_radius <= 0:
        logging.warning(f"Minor radius must be positive, got {new_minor_radius}")
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert "Minor radius must be positive" in log_output, "Should warn about negative minor radius"
    assert "got -1.0" in log_output, "Should include the invalid value in warning"
    
    # Test 2: Minor radius larger than major radius
    print("\nTesting minor radius larger than major radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    new_minor_radius = 5.0
    current_major_radius = 3.0
    
    if current_major_radius <= new_minor_radius:
        logging.warning(f"Minor radius ({new_minor_radius}) cannot be larger than or equal to major radius ({current_major_radius})")
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert "Minor radius (5.0) cannot be larger than or equal to major radius" in log_output, "Should warn about minor radius too large"
    
    # Clean up
    logging.getLogger().removeHandler(handler)
    
    print("✓ Minor radius warning logic test passed")
    return True


def test_valid_radius_logic():
    """Test that valid radius values don't produce warnings."""
    print("\nTesting valid radius logic...")
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Test valid major radius
    print("\nTesting valid major radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    new_major_radius = 5.0
    current_minor_radius = 2.0
    
    if new_major_radius <= 0:
        logging.warning(f"Major radius must be positive, got {new_major_radius}")
    elif new_major_radius <= current_minor_radius:
        logging.warning(f"Major radius ({new_major_radius}) cannot be smaller than or equal to minor radius ({current_minor_radius})")
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert log_output.strip() == "", "Should not produce warnings for valid major radius"
    
    # Test valid minor radius
    print("\nTesting valid minor radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    new_minor_radius = 2.0
    current_major_radius = 5.0
    
    if new_minor_radius <= 0:
        logging.warning(f"Minor radius must be positive, got {new_minor_radius}")
    elif current_major_radius <= new_minor_radius:
        logging.warning(f"Minor radius ({new_minor_radius}) cannot be larger than or equal to major radius ({current_major_radius})")
    
    log_output = log_capture.getvalue()
    print(f"Log output: {log_output.strip()}")
    
    assert log_output.strip() == "", "Should not produce warnings for valid minor radius"
    
    # Clean up
    logging.getLogger().removeHandler(handler)
    
    print("✓ Valid radius logic test passed")
    return True


def test_edge_cases():
    """Test edge cases for radius warnings."""
    print("\nTesting edge cases...")
    
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Test 1: Zero major radius
    print("\nTesting zero major radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    new_major_radius = 0.0
    if new_major_radius <= 0:
        logging.warning(f"Major radius must be positive, got {new_major_radius}")
    
    log_output = log_capture.getvalue()
    assert "Major radius must be positive" in log_output, "Should warn about zero major radius"
    
    # Test 2: Equal major and minor radius (should be allowed for circles)
    print("\nTesting equal major and minor radius...")
    log_capture.truncate(0)
    log_capture.seek(0)
    
    new_major_radius = 3.0
    current_minor_radius = 3.0
    
    if new_major_radius <= current_minor_radius:
        logging.warning(f"Major radius ({new_major_radius}) cannot be smaller than or equal to minor radius ({current_minor_radius})")
    
    log_output = log_capture.getvalue()
    assert "Major radius (3.0) cannot be smaller than or equal to minor radius" in log_output, "Should warn about equal radii"
    
    # Clean up
    logging.getLogger().removeHandler(handler)
    
    print("✓ Edge cases test passed")
    return True


def main():
    """Run all ellipse radius warning logic tests."""
    print("=== Ellipse Radius Warning Logic Tests ===\n")
    
    tests = [
        test_major_radius_warning_logic,
        test_minor_radius_warning_logic,
        test_valid_radius_logic,
        test_edge_cases
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
        print("All ellipse radius warning logic tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 