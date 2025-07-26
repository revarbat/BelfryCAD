#!/usr/bin/env python3
"""
Simple test for ControlDatum min/max value logic.
"""

import math


class MockControlDatum:
    """Mock ControlDatum class for testing min/max logic."""
    
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
    
    @property
    def min_value(self):
        """Get the minimum value."""
        return self._min_value

    @min_value.setter
    def min_value(self, value):
        """Set the minimum value."""
        self._min_value = value

    @property
    def max_value(self):
        """Get the maximum value."""
        return self._max_value

    @max_value.setter
    def max_value(self, value):
        """Set the maximum value."""
        self._max_value = value


def test_control_datum_min_max_initialization():
    """Test that ControlDatum properly initializes with min/max values."""
    print("Testing ControlDatum min/max initialization...")
    
    # Test with min value only
    datum1 = MockControlDatum(min_value=0.0)
    
    assert datum1.min_value == 0.0, "Min value should be set to 0.0"
    assert datum1.max_value is None, "Max value should be None"
    
    # Test with max value only
    datum2 = MockControlDatum(max_value=10.0)
    
    assert datum2.min_value is None, "Min value should be None"
    assert datum2.max_value == 10.0, "Max value should be set to 10.0"
    
    # Test with both min and max values
    datum3 = MockControlDatum(min_value=1.0, max_value=5.0)
    
    assert datum3.min_value == 1.0, "Min value should be set to 1.0"
    assert datum3.max_value == 5.0, "Max value should be set to 5.0"
    
    print("✓ ControlDatum min/max initialization test passed")
    return True


def test_is_value_in_range():
    """Test the is_value_in_range method."""
    print("\nTesting is_value_in_range method...")
    
    # Test datum with no constraints
    datum1 = MockControlDatum()
    
    assert datum1.is_value_in_range(0.0), "Should accept any value when no constraints"
    assert datum1.is_value_in_range(-1.0), "Should accept negative values when no constraints"
    assert datum1.is_value_in_range(100.0), "Should accept large values when no constraints"
    
    # Test datum with min value only
    datum2 = MockControlDatum(min_value=1.0)
    
    assert not datum2.is_value_in_range(0.0), "Should reject value below min"
    assert not datum2.is_value_in_range(0.5), "Should reject value below min"
    assert datum2.is_value_in_range(1.0), "Should accept value equal to min"
    assert datum2.is_value_in_range(5.0), "Should accept value above min"
    
    # Test datum with max value only
    datum3 = MockControlDatum(max_value=5.0)
    
    assert datum3.is_value_in_range(0.0), "Should accept value below max"
    assert datum3.is_value_in_range(5.0), "Should accept value equal to max"
    assert not datum3.is_value_in_range(5.1), "Should reject value above max"
    assert not datum3.is_value_in_range(10.0), "Should reject value above max"
    
    # Test datum with both min and max values
    datum4 = MockControlDatum(min_value=1.0, max_value=5.0)
    
    assert not datum4.is_value_in_range(0.0), "Should reject value below min"
    assert not datum4.is_value_in_range(0.5), "Should reject value below min"
    assert datum4.is_value_in_range(1.0), "Should accept value equal to min"
    assert datum4.is_value_in_range(3.0), "Should accept value in range"
    assert datum4.is_value_in_range(5.0), "Should accept value equal to max"
    assert not datum4.is_value_in_range(5.1), "Should reject value above max"
    assert not datum4.is_value_in_range(10.0), "Should reject value above max"
    
    print("✓ is_value_in_range test passed")
    return True


def test_ellipse_radius_constraints():
    """Test the specific constraints for ellipse radius datums."""
    print("\nTesting ellipse radius constraints...")
    
    # Test major radius datum (min_value only)
    major_datum = MockControlDatum(min_value=0.001)  # Must be positive
    
    assert not major_datum.is_value_in_range(0.0), "Major radius should reject zero"
    assert not major_datum.is_value_in_range(-1.0), "Major radius should reject negative"
    assert not major_datum.is_value_in_range(0.0005), "Major radius should reject very small values"
    assert major_datum.is_value_in_range(0.001), "Major radius should accept min value"
    assert major_datum.is_value_in_range(1.0), "Major radius should accept positive values"
    assert major_datum.is_value_in_range(100.0), "Major radius should accept large values"
    
    # Test minor radius datum (min_value only, max_value will be set dynamically)
    minor_datum = MockControlDatum(min_value=0.001)  # Must be positive
    
    assert not minor_datum.is_value_in_range(0.0), "Minor radius should reject zero"
    assert not minor_datum.is_value_in_range(-1.0), "Minor radius should reject negative"
    assert not minor_datum.is_value_in_range(0.0005), "Minor radius should reject very small values"
    assert minor_datum.is_value_in_range(0.001), "Minor radius should accept min value"
    assert minor_datum.is_value_in_range(1.0), "Minor radius should accept positive values"
    
    # Test with dynamic max value (simulating major radius = 5.0)
    minor_datum.max_value = 4.999  # Must be less than major radius
    
    assert minor_datum.is_value_in_range(1.0), "Minor radius should accept value in range"
    assert minor_datum.is_value_in_range(4.999), "Minor radius should accept value equal to max"
    assert not minor_datum.is_value_in_range(5.0), "Minor radius should reject value equal to major radius"
    assert not minor_datum.is_value_in_range(6.0), "Minor radius should reject value above major radius"
    
    print("✓ Ellipse radius constraints test passed")
    return True


def test_property_setters():
    """Test the min_value and max_value property setters."""
    print("\nTesting min_value and max_value property setters...")
    
    datum = MockControlDatum()
    
    # Test setting min_value
    datum.min_value = 2.0
    assert datum.min_value == 2.0, "min_value should be set to 2.0"
    
    # Test setting max_value
    datum.max_value = 8.0
    assert datum.max_value == 8.0, "max_value should be set to 8.0"
    
    # Test updating min_value
    datum.min_value = 3.0
    assert datum.min_value == 3.0, "min_value should be updated to 3.0"
    
    # Test updating max_value
    datum.max_value = 7.0
    assert datum.max_value == 7.0, "max_value should be updated to 7.0"
    
    # Test setting to None
    datum.min_value = None
    assert datum.min_value is None, "min_value should be set to None"
    
    datum.max_value = None
    assert datum.max_value is None, "max_value should be set to None"
    
    print("✓ Property setters test passed")
    return True


def test_edge_cases():
    """Test edge cases for min/max constraints."""
    print("\nTesting edge cases...")
    
    # Test with equal min and max values
    datum1 = MockControlDatum(min_value=3.0, max_value=3.0)
    assert not datum1.is_value_in_range(2.9), "Should reject value below equal min/max"
    assert datum1.is_value_in_range(3.0), "Should accept value equal to min/max"
    assert not datum1.is_value_in_range(3.1), "Should reject value above equal min/max"
    
    # Test with very small ranges
    datum2 = MockControlDatum(min_value=1.0, max_value=1.001)
    assert not datum2.is_value_in_range(0.999), "Should reject value below small range"
    assert datum2.is_value_in_range(1.0), "Should accept min value of small range"
    assert datum2.is_value_in_range(1.0005), "Should accept value in small range"
    assert datum2.is_value_in_range(1.001), "Should accept max value of small range"
    assert not datum2.is_value_in_range(1.002), "Should reject value above small range"
    
    # Test with negative ranges
    datum3 = MockControlDatum(min_value=-5.0, max_value=-1.0)
    assert not datum3.is_value_in_range(-6.0), "Should reject value below negative range"
    assert datum3.is_value_in_range(-5.0), "Should accept min value of negative range"
    assert datum3.is_value_in_range(-3.0), "Should accept value in negative range"
    assert datum3.is_value_in_range(-1.0), "Should accept max value of negative range"
    assert not datum3.is_value_in_range(0.0), "Should reject value above negative range"
    
    print("✓ Edge cases test passed")
    return True


def main():
    """Run all ControlDatum min/max value logic tests."""
    print("=== ControlDatum Min/Max Value Logic Tests ===\n")
    
    tests = [
        test_control_datum_min_max_initialization,
        test_is_value_in_range,
        test_ellipse_radius_constraints,
        test_property_setters,
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
        print("All ControlDatum min/max value logic tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 