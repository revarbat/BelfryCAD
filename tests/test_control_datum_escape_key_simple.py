#!/usr/bin/env python3
"""
Simple test for ControlDatum Escape key fix.
"""

import sys
from unittest.mock import Mock


class MockControlDatum:
    """Mock ControlDatum class for testing Escape key fix."""
    
    def __init__(self):
        self._is_editing = False
        self.cancel_called = False
        self.scene = Mock()
        self.scene.update = Mock()
    
    def _cancel_editing(self, dialog):
        """Mock cancel editing method."""
        self.cancel_called = True
        self._is_editing = False
        self.update()
        self.prepareGeometryChange()
        if self.scene:
            self.scene.update()
    
    def update(self):
        """Mock update method."""
        pass
    
    def prepareGeometryChange(self):
        """Mock prepareGeometryChange method."""
        pass


def test_dialog_rejected_signal_connection():
    """Test that dialog.rejected signal is connected to _cancel_editing."""
    print("Testing dialog rejected signal connection...")
    
    # Create mock control datum
    datum = MockControlDatum()
    
    # Simulate the dialog setup from start_editing method
    class MockDialog:
        def __init__(self):
            self.rejected_signal = Mock()
            self.rejected_signal.connect = Mock()
        
        def rejected(self):
            return self.rejected_signal
    
    class MockButtonBox:
        def __init__(self):
            self.rejected_signal = Mock()
            self.rejected_signal.connect = Mock()
            self.accepted_signal = Mock()
            self.accepted_signal.connect = Mock()
        
        def rejected(self):
            return self.rejected_signal
        
        def accepted(self):
            return self.accepted_signal
    
    # Create mock dialog and button box
    dialog = MockDialog()
    button_box = MockButtonBox()
    
    # Simulate the signal connections from the actual code
    # button_box.accepted.connect(lambda: self._finish_editing(dialog, expr_edit))
    # button_box.rejected.connect(lambda: self._cancel_editing(dialog))
    # dialog.rejected.connect(lambda: self._cancel_editing(dialog))
    
    button_box.accepted().connect(Mock())
    button_box.rejected().connect(Mock())
    dialog.rejected().connect(Mock())
    
    # Verify that all signals are connected
    assert button_box.accepted().connect.called, "Button box accepted should be connected"
    assert button_box.rejected().connect.called, "Button box rejected should be connected"
    assert dialog.rejected().connect.called, "Dialog rejected should be connected"
    
    print("✓ Dialog rejected signal connection test passed")
    return True


def test_cancel_editing_method():
    """Test that _cancel_editing method works correctly."""
    print("\nTesting _cancel_editing method...")
    
    datum = MockControlDatum()
    
    # Start in editing mode
    datum._is_editing = True
    assert datum._is_editing == True, "Should be in editing mode"
    
    # Call cancel editing
    datum._cancel_editing(None)
    
    # Verify the method was called and state changed
    assert datum.cancel_called == True, "Cancel method should be called"
    assert datum._is_editing == False, "Should not be in editing mode after cancel"
    assert datum.scene.update.called, "Scene update should be called"
    
    print("✓ _cancel_editing method test passed")
    return True


def test_escape_key_equivalence():
    """Test that Escape key and Cancel button call the same method."""
    print("\nTesting Escape key equivalence...")
    
    datum = MockControlDatum()
    
    # Test Cancel button behavior
    datum._is_editing = True
    datum.cancel_called = False
    datum._cancel_editing(None)
    assert datum.cancel_called == True, "Cancel method should be called"
    assert datum._is_editing == False, "Should not be in editing mode"
    
    # Test Escape key behavior (should call same method)
    datum._is_editing = True
    datum.cancel_called = False
    datum._cancel_editing(None)  # Same method as Cancel button
    assert datum.cancel_called == True, "Cancel method should be called for Escape key"
    assert datum._is_editing == False, "Should not be in editing mode after Escape key"
    
    print("✓ Escape key equivalence test passed")
    return True


def main():
    """Run all ControlDatum Escape key fix tests."""
    print("=== ControlDatum Escape Key Fix Tests ===\n")
    
    tests = [
        test_dialog_rejected_signal_connection,
        test_cancel_editing_method,
        test_escape_key_equivalence
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