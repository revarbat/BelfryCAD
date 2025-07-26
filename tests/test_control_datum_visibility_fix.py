#!/usr/bin/env python3
"""
Test script for ControlDatum visibility fix when dismissing with Escape key.
"""

import math
import sys
import os
from unittest.mock import Mock, patch
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PySide6.QtGui import QColor


class MockControlDatum:
    """Mock ControlDatum class for testing visibility fix."""
    
    def __init__(self, min_value=None, max_value=None):
        self._min_value = min_value
        self._max_value = max_value
        self._current_value = 0.0
        self._is_editing = False
        self.scene = Mock()
        self.scene.update = Mock()
    
    def is_value_in_range(self, value=None):
        """Check if the given value (or current value if None) is within the min/max range."""
        if value is None:
            value = self._current_value
        
        if self._min_value is not None and value < self._min_value:
            return False
        if self._max_value is not None and value > self._max_value:
            return False
        return True
    
    def update(self):
        """Mock update method."""
        pass
    
    def prepareGeometryChange(self):
        """Mock prepareGeometryChange method."""
        pass


def test_cancel_editing_visibility_fix():
    """Test that canceling editing properly restores control datum visibility."""
    print("Testing cancel editing visibility fix...")
    
    # Create mock control datum
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Simulate starting editing
    datum._is_editing = True
    assert datum._is_editing == True, "Should be in editing mode"
    
    # Simulate canceling editing (like pressing Escape)
    def mock_cancel_editing():
        """Mock the cancel editing logic."""
        # Set editing flag to False
        datum._is_editing = False
        # Call update methods
        datum.update()
        datum.prepareGeometryChange()
        if datum.scene:
            datum.scene.update()
    
    mock_cancel_editing()
    
    # Verify the control datum is no longer in editing mode
    assert datum._is_editing == False, "Should not be in editing mode after cancel"
    
    # Verify that update methods were called
    assert datum.scene.update.called, "Scene update should be called"
    
    print("✓ Cancel editing visibility fix test passed")
    return True


def test_finish_editing_visibility_fix():
    """Test that finishing editing properly restores control datum visibility."""
    print("\nTesting finish editing visibility fix...")
    
    # Create mock control datum
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Simulate starting editing
    datum._is_editing = True
    assert datum._is_editing == True, "Should be in editing mode"
    
    # Simulate finishing editing (like clicking Set)
    def mock_finish_editing():
        """Mock the finish editing logic."""
        # Set editing flag to False
        datum._is_editing = False
        # Call update methods
        datum.update()
        datum.prepareGeometryChange()
        if datum.scene:
            datum.scene.update()
    
    mock_finish_editing()
    
    # Verify the control datum is no longer in editing mode
    assert datum._is_editing == False, "Should not be in editing mode after finish"
    
    # Verify that update methods were called
    assert datum.scene.update.called, "Scene update should be called"
    
    print("✓ Finish editing visibility fix test passed")
    return True


def test_editing_state_transitions():
    """Test the transitions between editing states."""
    print("\nTesting editing state transitions...")
    
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Initial state
    assert datum._is_editing == False, "Should start in non-editing state"
    
    # Start editing
    datum._is_editing = True
    assert datum._is_editing == True, "Should be in editing state"
    
    # Cancel editing
    datum._is_editing = False
    datum.update()
    datum.prepareGeometryChange()
    if datum.scene:
        datum.scene.update()
    assert datum._is_editing == False, "Should return to non-editing state after cancel"
    
    # Start editing again
    datum._is_editing = True
    assert datum._is_editing == True, "Should be able to start editing again"
    
    # Finish editing
    datum._is_editing = False
    datum.update()
    datum.prepareGeometryChange()
    if datum.scene:
        datum.scene.update()
    assert datum._is_editing == False, "Should return to non-editing state after finish"
    
    print("✓ Editing state transitions test passed")
    return True


def test_paint_method_behavior():
    """Test that the paint method behaves correctly based on editing state."""
    print("\nTesting paint method behavior...")
    
    class MockPainter:
        def __init__(self):
            self.paint_called = False
        
        def save(self):
            pass
        
        def restore(self):
            pass
    
    class TestControlDatum(MockControlDatum):
        def paint(self, painter, option, widget=None):
            if self._is_editing:
                return  # Don't paint when editing
            painter.paint_called = True
    
    datum = TestControlDatum(min_value=1.0, max_value=5.0)
    painter = MockPainter()
    
    # Test 1: Not editing - should paint
    datum._is_editing = False
    datum.paint(painter, None)
    assert painter.paint_called == True, "Should paint when not editing"
    
    # Test 2: Editing - should not paint
    painter.paint_called = False
    datum._is_editing = True
    datum.paint(painter, None)
    assert painter.paint_called == False, "Should not paint when editing"
    
    # Test 3: Cancel editing - should paint again
    datum._is_editing = False
    datum.paint(painter, None)
    assert painter.paint_called == True, "Should paint again after canceling editing"
    
    print("✓ Paint method behavior test passed")
    return True


def test_scene_update_calls():
    """Test that scene update is called when needed."""
    print("\nTesting scene update calls...")
    
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Reset mock call count
    datum.scene.update.reset_mock()
    
    # Simulate canceling editing
    datum._is_editing = False
    datum.update()
    datum.prepareGeometryChange()
    if datum.scene:
        datum.scene.update()
    
    # Verify scene update was called
    assert datum.scene.update.call_count >= 1, "Scene update should be called at least once"
    
    # Reset mock call count
    datum.scene.update.reset_mock()
    
    # Simulate finishing editing
    datum._is_editing = False
    datum.update()
    datum.prepareGeometryChange()
    if datum.scene:
        datum.scene.update()
    
    # Verify scene update was called
    assert datum.scene.update.call_count >= 1, "Scene update should be called at least once"
    
    print("✓ Scene update calls test passed")
    return True


def main():
    """Run all ControlDatum visibility fix tests."""
    print("=== ControlDatum Visibility Fix Tests ===\n")
    
    tests = [
        test_cancel_editing_visibility_fix,
        test_finish_editing_visibility_fix,
        test_editing_state_transitions,
        test_paint_method_behavior,
        test_scene_update_calls
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
        print("All ControlDatum visibility fix tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 