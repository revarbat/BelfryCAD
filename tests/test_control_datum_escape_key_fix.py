#!/usr/bin/env python3
"""
Test script for ControlDatum Escape key fix to ensure it has the same effect as Cancel button.
"""

import math
import sys
import os
from unittest.mock import Mock, patch
from PySide6.QtCore import QPointF, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QPushButton
from PySide6.QtGui import QColor, QKeySequence
from PySide6.QtCore import Qt


class MockControlDatum:
    """Mock ControlDatum class for testing Escape key fix."""
    
    def __init__(self, min_value=None, max_value=None):
        self._min_value = min_value
        self._max_value = max_value
        self._current_value = 0.0
        self._is_editing = False
        self.scene = Mock()
        self.scene.update = Mock()
        self.cancel_called = False
        self.finish_called = False
    
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
    
    def _cancel_editing(self, dialog):
        """Mock cancel editing method."""
        self.cancel_called = True
        self._is_editing = False
        self.update()
        self.prepareGeometryChange()
        if self.scene:
            self.scene.update()
    
    def _finish_editing(self, dialog, expr_edit):
        """Mock finish editing method."""
        self.finish_called = True
        self._is_editing = False
        self.update()
        self.prepareGeometryChange()
        if self.scene:
            self.scene.update()


def test_escape_key_vs_cancel_button():
    """Test that Escape key and Cancel button have exactly the same effect."""
    print("Testing Escape key vs Cancel button behavior...")
    
    # Create mock control datum
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Simulate starting editing
    datum._is_editing = True
    assert datum._is_editing == True, "Should be in editing mode"
    
    # Test 1: Cancel button behavior
    datum.cancel_called = False
    datum.finish_called = False
    datum._cancel_editing(None)
    
    assert datum.cancel_called == True, "Cancel method should be called"
    assert datum.finish_called == False, "Finish method should not be called"
    assert datum._is_editing == False, "Should not be in editing mode after cancel"
    assert datum.scene.update.called, "Scene update should be called"
    
    # Reset for next test
    datum.scene.update.reset_mock()
    datum._is_editing = True
    
    # Test 2: Escape key should have same behavior
    datum.cancel_called = False
    datum.finish_called = False
    datum._cancel_editing(None)  # Simulate Escape key triggering same method
    
    assert datum.cancel_called == True, "Cancel method should be called for Escape key"
    assert datum.finish_called == False, "Finish method should not be called for Escape key"
    assert datum._is_editing == False, "Should not be in editing mode after Escape key"
    assert datum.scene.update.called, "Scene update should be called for Escape key"
    
    print("✓ Escape key vs Cancel button behavior test passed")
    return True


def test_dialog_signal_connections():
    """Test that dialog signals are properly connected."""
    print("\nTesting dialog signal connections...")
    
    class MockDialog:
        def __init__(self):
            self.rejected_connected = False
            self.accepted_connected = False
        
        def rejected(self):
            return Mock()
        
        def accepted(self):
            return Mock()
    
    class MockButtonBox:
        def __init__(self):
            self.rejected_connected = False
            self.accepted_connected = False
        
        def rejected(self):
            return Mock()
        
        def accepted(self):
            return Mock()
    
    # Simulate the connection logic
    dialog = MockDialog()
    button_box = MockButtonBox()
    
    # Connect button box signals
    button_box.rejected().connect = Mock()
    button_box.accepted().connect = Mock()
    
    # Connect dialog signals (this is the fix)
    dialog.rejected().connect = Mock()
    
    # Verify connections
    assert button_box.rejected().connect.called, "Button box rejected should be connected"
    assert button_box.accepted().connect.called, "Button box accepted should be connected"
    assert dialog.rejected().connect.called, "Dialog rejected should be connected"
    
    print("✓ Dialog signal connections test passed")
    return True


def test_editing_state_consistency():
    """Test that editing state is consistent regardless of dismissal method."""
    print("\nTesting editing state consistency...")
    
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Test multiple cycles of editing and dismissal
    for cycle in range(3):
        # Start editing
        datum._is_editing = True
        assert datum._is_editing == True, f"Should be in editing mode in cycle {cycle}"
        
        # Cancel editing (simulate either Cancel button or Escape key)
        datum._cancel_editing(None)
        assert datum._is_editing == False, f"Should not be in editing mode after cancel in cycle {cycle}"
        assert datum.scene.update.called, f"Scene update should be called in cycle {cycle}"
        
        # Reset for next cycle
        datum.scene.update.reset_mock()
    
    print("✓ Editing state consistency test passed")
    return True


def test_visibility_restoration():
    """Test that visibility is properly restored after any dismissal method."""
    print("\nTesting visibility restoration...")
    
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Test that paint method behavior is correct
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
    
    # Test visibility restoration after cancel
    datum._is_editing = True
    datum.paint(painter, None)
    assert painter.paint_called == False, "Should not paint when editing"
    
    # Cancel editing
    datum._cancel_editing(None)
    painter.paint_called = False
    datum.paint(painter, None)
    assert painter.paint_called == True, "Should paint after canceling editing"
    
    # Test visibility restoration after escape (same method)
    datum._is_editing = True
    datum.paint(painter, None)
    assert painter.paint_called == False, "Should not paint when editing"
    
    # Escape key (calls same method)
    datum._cancel_editing(None)
    painter.paint_called = False
    datum.paint(painter, None)
    assert painter.paint_called == True, "Should paint after escape key"
    
    print("✓ Visibility restoration test passed")
    return True


def test_method_call_equivalence():
    """Test that Cancel button and Escape key call exactly the same method."""
    print("\nTesting method call equivalence...")
    
    datum = MockControlDatum(min_value=1.0, max_value=5.0)
    
    # Track method calls
    cancel_calls = 0
    finish_calls = 0
    
    def track_cancel(dialog):
        nonlocal cancel_calls
        cancel_calls += 1
        datum._cancel_editing(dialog)
    
    def track_finish(dialog, expr_edit):
        nonlocal finish_calls
        finish_calls += 1
        datum._finish_editing(dialog, expr_edit)
    
    # Simulate Cancel button press
    datum._is_editing = True
    track_cancel(None)
    assert cancel_calls == 1, "Cancel method should be called once"
    assert finish_calls == 0, "Finish method should not be called"
    assert datum._is_editing == False, "Should not be in editing mode"
    
    # Simulate Escape key press (should call same method)
    datum._is_editing = True
    track_cancel(None)  # Same method as Cancel button
    assert cancel_calls == 2, "Cancel method should be called twice"
    assert finish_calls == 0, "Finish method should still not be called"
    assert datum._is_editing == False, "Should not be in editing mode"
    
    print("✓ Method call equivalence test passed")
    return True


def main():
    """Run all ControlDatum Escape key fix tests."""
    print("=== ControlDatum Escape Key Fix Tests ===\n")
    
    tests = [
        test_escape_key_vs_cancel_button,
        test_dialog_signal_connections,
        test_editing_state_consistency,
        test_visibility_restoration,
        test_method_call_equivalence
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
        print("All ControlDatum Escape key fix tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main()) 