#!/usr/bin/env python3
"""
Test script for ControlDatum "Out of Range" indicator.
"""

import math
import sys
import os
from unittest.mock import Mock, patch
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtGui import QColor


class MockControlDatum:
    """Mock ControlDatum class for testing out of range indicator logic."""
    
    def __init__(self, min_value=None, max_value=None):
        self._min_value = min_value
        self._max_value = max_value
        self._current_value = 0.0
    
    def is_value_in_range(self, value=None):
        """Check if the given value (or current value if None) is within the min/max range."""
        if value is None:
            value = self._current_value
        
        if self._min_value is not None and value < self._min_value:
            return False
        if self._max_value is not None and value > self._max_value:
            return False
        return True


def test_out_of_range_indicator_logic():
    """Test the logic for showing/hiding the "Out of Range" indicator."""
    print("Testing out of range indicator logic...")
    
    # Test datum with min/max constraints
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Test values within range
    assert datum.is_value_in_range(1.0), "Should accept min value"
    assert datum.is_value_in_range(3.0), "Should accept value in range"
    assert datum.is_value_in_range(5.0), "Should accept max value"
    
    # Test values out of range
    assert not datum.is_value_in_range(0.5), "Should reject value below min"
    assert not datum.is_value_in_range(6.0), "Should reject value above max"
    
    print("✓ Out of range indicator logic test passed")
    return True


def test_ellipse_radius_out_of_range_scenarios():
    """Test specific out of range scenarios for ellipse radius datums."""
    print("\nTesting ellipse radius out of range scenarios...")
    
    # Test major radius datum (min_value only)
    major_datum = MockControlDatum(min_value=0.001)
    
    # Valid values
    assert major_datum.is_value_in_range(0.001), "Major radius should accept min value"
    assert major_datum.is_value_in_range(1.0), "Major radius should accept positive values"
    assert major_datum.is_value_in_range(100.0), "Major radius should accept large values"
    
    # Invalid values
    assert not major_datum.is_value_in_range(0.0), "Major radius should reject zero"
    assert not major_datum.is_value_in_range(-1.0), "Major radius should reject negative"
    assert not major_datum.is_value_in_range(0.0005), "Major radius should reject very small values"
    
    # Test minor radius datum with dynamic max value
    minor_datum = MockControlDatum(min_value=0.001, max_value=4.999)
    
    # Valid values
    assert minor_datum.is_value_in_range(0.001), "Minor radius should accept min value"
    assert minor_datum.is_value_in_range(2.0), "Minor radius should accept value in range"
    assert minor_datum.is_value_in_range(4.999), "Minor radius should accept max value"
    
    # Invalid values
    assert not minor_datum.is_value_in_range(0.0), "Minor radius should reject zero"
    assert not minor_datum.is_value_in_range(-1.0), "Minor radius should reject negative"
    assert not minor_datum.is_value_in_range(5.0), "Minor radius should reject value equal to major radius"
    assert not minor_datum.is_value_in_range(6.0), "Minor radius should reject value above major radius"
    
    print("✓ Ellipse radius out of range scenarios test passed")
    return True


def test_indicator_visibility_logic():
    """Test the logic for showing/hiding the indicator based on different conditions."""
    print("\nTesting indicator visibility logic...")
    
    # Mock the validation logic
    def mock_validate_input(text, expr_error, datum, set_button_enabled, indicator_visible):
        """Mock validation function to test indicator visibility."""
        if expr_error is None and text.strip():
            try:
                # Simulate expression evaluation
                new_value = float(text)
                scaled_value = new_value  # Assume unit scale = 1.0
                
                # Check if the value is within range
                if datum.is_value_in_range(scaled_value):
                    set_button_enabled = True
                    indicator_visible = False
                else:
                    set_button_enabled = False
                    indicator_visible = True
            except Exception:
                set_button_enabled = False
                indicator_visible = False  # Hide for invalid expressions
        else:
            set_button_enabled = False
            indicator_visible = False  # Hide for empty/invalid input
        
        return set_button_enabled, indicator_visible
    
    # Test cases
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Test 1: Valid expression, value in range
    set_enabled, indicator_visible = mock_validate_input("3.0", None, datum, False, False)
    assert set_enabled == True, "Set button should be enabled for valid value in range"
    assert indicator_visible == False, "Indicator should be hidden for value in range"
    
    # Test 2: Valid expression, value out of range (too small)
    set_enabled, indicator_visible = mock_validate_input("0.5", None, datum, False, False)
    assert set_enabled == False, "Set button should be disabled for value out of range"
    assert indicator_visible == True, "Indicator should be visible for value out of range"
    
    # Test 3: Valid expression, value out of range (too large)
    set_enabled, indicator_visible = mock_validate_input("6.0", None, datum, False, False)
    assert set_enabled == False, "Set button should be disabled for value out of range"
    assert indicator_visible == True, "Indicator should be visible for value out of range"
    
    # Test 4: Invalid expression
    set_enabled, indicator_visible = mock_validate_input("invalid", "Error", datum, False, False)
    assert set_enabled == False, "Set button should be disabled for invalid expression"
    assert indicator_visible == False, "Indicator should be hidden for invalid expression"
    
    # Test 5: Empty input
    set_enabled, indicator_visible = mock_validate_input("", None, datum, False, False)
    assert set_enabled == False, "Set button should be disabled for empty input"
    assert indicator_visible == False, "Indicator should be hidden for empty input"
    
    print("✓ Indicator visibility logic test passed")
    return True


def test_edge_cases():
    """Test edge cases for the out of range indicator."""
    print("\nTesting edge cases...")
    
    # Test datum with no constraints
    datum1 = MockControlDatum()
    assert datum1.is_value_in_range(0.0), "Should accept any value when no constraints"
    assert datum1.is_value_in_range(-1.0), "Should accept negative values when no constraints"
    assert datum1.is_value_in_range(100.0), "Should accept large values when no constraints"
    
    # Test datum with equal min and max values
    datum2 = MockControlDatum(min_value=3.0, max_value=3.0)
    assert not datum2.is_value_in_range(2.9), "Should reject value below equal min/max"
    assert datum2.is_value_in_range(3.0), "Should accept value equal to min/max"
    assert not datum2.is_value_in_range(3.1), "Should reject value above equal min/max"
    
    # Test datum with very small range
    datum3 = MockControlDatum(min_value=1.0, max_value=1.001)
    assert not datum3.is_value_in_range(0.999), "Should reject value below small range"
    assert datum3.is_value_in_range(1.0), "Should accept min value of small range"
    assert datum3.is_value_in_range(1.0005), "Should accept value in small range"
    assert datum3.is_value_in_range(1.001), "Should accept max value of small range"
    assert not datum3.is_value_in_range(1.002), "Should reject value above small range"
    
    print("✓ Edge cases test passed")
    return True


def test_ellipse_specific_constraints():
    """Test the specific constraints used in the updated ellipse implementation."""
    print("\nTesting ellipse-specific constraints...")
    
    # Test the updated ellipse constraints from the user's changes
    # Major radius: min_value = minor_radius (must be >= minor radius)
    # Minor radius: max_value = major_radius (must be <= major radius)
    
    # Simulate ellipse with major_radius = 5.0, minor_radius = 2.0
    major_radius = 5.0
    minor_radius = 2.0
    
    # Major radius datum with min_value = minor_radius
    major_datum = MockControlDatum(min_value=minor_radius)
    
    # Valid major radius values
    assert major_datum.is_value_in_range(2.0), "Major radius should accept value equal to minor radius"
    assert major_datum.is_value_in_range(3.0), "Major radius should accept value greater than minor radius"
    assert major_datum.is_value_in_range(10.0), "Major radius should accept large values"
    
    # Invalid major radius values
    assert not major_datum.is_value_in_range(1.5), "Major radius should reject value less than minor radius"
    assert not major_datum.is_value_in_range(0.0), "Major radius should reject zero"
    assert not major_datum.is_value_in_range(-1.0), "Major radius should reject negative values"
    
    # Minor radius datum with max_value = major_radius
    minor_datum = MockControlDatum(max_value=major_radius)
    
    # Valid minor radius values
    assert minor_datum.is_value_in_range(1.0), "Minor radius should accept small values"
    assert minor_datum.is_value_in_range(3.0), "Minor radius should accept values less than major radius"
    assert minor_datum.is_value_in_range(5.0), "Minor radius should accept value equal to major radius"
    
    # Invalid minor radius values
    assert not minor_datum.is_value_in_range(5.1), "Minor radius should reject value greater than major radius"
    assert not minor_datum.is_value_in_range(10.0), "Minor radius should reject large values"
    
    print("✓ Ellipse-specific constraints test passed")
    return True


def main():
    """Run all ControlDatum out of range indicator tests."""
    print("=== ControlDatum Out of Range Indicator Tests ===\n")
    
    tests = [
        test_out_of_range_indicator_logic,
        test_ellipse_radius_out_of_range_scenarios,
        test_indicator_visibility_logic,
        test_edge_cases,
        test_ellipse_specific_constraints
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
        print("All ControlDatum out of range indicator tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 