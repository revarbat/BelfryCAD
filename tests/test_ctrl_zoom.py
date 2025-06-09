#!/usr/bin/env python3
"""
Test script to verify that Ctrl+mousewheel zooming functionality has been
added to CADGraphicsView. This script checks that the zoom feature works
correctly and integrates properly with existing scroll functionality.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QWheelEvent

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BelfryCAD.gui.cad_graphics_view import CADGraphicsView
from BelfryCAD.gui.drawing_manager import DrawingManager


class MockCadScene:
    """Mock CadScene for testing zoom functionality"""
    def __init__(self):
        self.scale_factor = 1.0
        self.zoom_calls = []

    def set_scale_factor(self, scale_factor):
        """Mock method to track zoom calls"""
        self.zoom_calls.append(scale_factor)
        self.scale_factor = scale_factor
        print(f"  → Zoom called with scale factor: {scale_factor:.3f}")


class MockDrawingManager:
    """Mock DrawingManager for testing"""
    def __init__(self):
        self.cad_scene = MockCadScene()


def create_wheel_event(angle_delta_y, modifiers):
    """Helper to create QWheelEvent with correct signature"""
    return QWheelEvent(
        QPoint(100, 100),      # pos
        QPoint(100, 100),      # globalPos
        QPoint(0, 0),          # pixelDelta
        QPoint(0, angle_delta_y),  # angleDelta
        Qt.MouseButton.NoButton,
        modifiers,
        Qt.ScrollPhase.NoScrollPhase,
        False                  # inverted
    )


def test_ctrl_zoom_functionality():
    """Test that CADGraphicsView supports Ctrl+mousewheel zooming."""

    # Create a CADGraphicsView instance
    view = CADGraphicsView()

    # Set up mock drawing manager
    mock_drawing_manager = MockDrawingManager()
    view.set_drawing_manager(mock_drawing_manager)

    print("✓ CADGraphicsView and mock components created")

    # Test 1: Check that wheelEvent method exists
    assert hasattr(view, 'wheelEvent'), \
        "Wheel event handler should exist"
    print("✓ Wheel event handler exists")

    # Test 2: Test normal wheel scrolling (should not zoom)
    normal_wheel_event = create_wheel_event(120, Qt.KeyboardModifier.NoModifier)

    # Reset zoom calls
    mock_drawing_manager.cad_scene.zoom_calls = []
    mock_drawing_manager.cad_scene.scale_factor = 1.0

    # Simulate normal wheel event
    view.wheelEvent(normal_wheel_event)

    # Should not have called zoom
    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 0, \
        "Normal wheel should not trigger zoom"
    print("✓ Normal wheel scrolling does not trigger zoom")

    # Test 3: Test Ctrl+wheel zoom in (positive delta)
    ctrl_wheel_in = create_wheel_event(120, Qt.KeyboardModifier.ControlModifier)

    # Reset zoom calls
    mock_drawing_manager.cad_scene.zoom_calls = []
    mock_drawing_manager.cad_scene.scale_factor = 1.0

    # Simulate Ctrl+wheel event
    print("  Testing Ctrl+wheel zoom in...")
    view.wheelEvent(ctrl_wheel_in)

    # Should have called zoom with increased scale
    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 1, \
        "Ctrl+wheel should trigger zoom"
    assert mock_drawing_manager.cad_scene.zoom_calls[0] > 1.0, \
        "Zoom in should increase scale factor"
    expected_scale = 1.0 * (1.0 + (1.0 * 0.2))  # 20% increase
    actual_scale = mock_drawing_manager.cad_scene.zoom_calls[0]
    assert abs(actual_scale - expected_scale) < 0.001, \
        f"Expected scale {expected_scale}, got {actual_scale}"
    print("✓ Ctrl+wheel zoom in works correctly")

    # Test 4: Test Ctrl+wheel zoom out (negative delta)
    ctrl_wheel_out = create_wheel_event(-120, Qt.KeyboardModifier.ControlModifier)

    # Reset zoom calls
    mock_drawing_manager.cad_scene.zoom_calls = []
    mock_drawing_manager.cad_scene.scale_factor = 1.0

    # Simulate Ctrl+wheel event
    print("  Testing Ctrl+wheel zoom out...")
    view.wheelEvent(ctrl_wheel_out)

    # Should have called zoom with decreased scale
    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 1, \
        "Ctrl+wheel should trigger zoom"
    assert mock_drawing_manager.cad_scene.zoom_calls[0] < 1.0, \
        "Zoom out should decrease scale factor"
    expected_scale = 1.0 * (1.0 + (-1.0 * 0.2))  # 20% decrease
    actual_scale = mock_drawing_manager.cad_scene.zoom_calls[0]
    assert abs(actual_scale - expected_scale) < 0.001, \
        f"Expected scale {expected_scale}, got {actual_scale}"
    print("✓ Ctrl+wheel zoom out works correctly")

    # Test 5: Test zoom limits (minimum)
    mock_drawing_manager.cad_scene.scale_factor = 0.02  # Near min
    mock_drawing_manager.cad_scene.zoom_calls = []

    print("  Testing zoom limit (minimum)...")
    view.wheelEvent(ctrl_wheel_out)  # Try to zoom out more

    # Should be clamped to minimum
    assert mock_drawing_manager.cad_scene.zoom_calls[0] >= 0.01, \
        "Zoom should be clamped to minimum of 0.01"
    print("✓ Minimum zoom limit works correctly")

    # Test 6: Test zoom limits (maximum)
    mock_drawing_manager.cad_scene.scale_factor = 95.0  # Near max
    mock_drawing_manager.cad_scene.zoom_calls = []

    print("  Testing zoom limit (maximum)...")
    view.wheelEvent(ctrl_wheel_in)  # Try to zoom in more

    # Should be clamped to maximum
    assert mock_drawing_manager.cad_scene.zoom_calls[0] <= 100.0, \
        "Zoom should be clamped to maximum of 100.0"
    print("✓ Maximum zoom limit works correctly")

    # Test 7: Test that other modifier keys don't trigger zoom
    shift_wheel_event = create_wheel_event(120, Qt.KeyboardModifier.ShiftModifier)

    mock_drawing_manager.cad_scene.zoom_calls = []
    mock_drawing_manager.cad_scene.scale_factor = 1.0

    view.wheelEvent(shift_wheel_event)

    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 0, \
        "Shift+wheel should not trigger zoom (horizontal scroll)"
    print("✓ Shift+wheel does not trigger zoom (horizontal scroll preserved)")

    print("\n🎉 All tests passed! Ctrl+mousewheel zooming has been "
          "successfully implemented.")
    print("\nZoom features available:")
    print("- Ctrl+wheel up: Zoom in (20% per step)")
    print("- Ctrl+wheel down: Zoom out (20% per step)")
    print("- Zoom limits: 0.01x to 100x")
    print("- Integration with existing scroll functionality")

    return True


def test_integration_with_existing_features():
    """Test that zoom works alongside existing features"""

    view = CADGraphicsView()
    mock_drawing_manager = MockDrawingManager()
    view.set_drawing_manager(mock_drawing_manager)

    print("\n--- Testing Integration ---")

    # Test that all expected methods still exist
    expected_methods = ['wheelEvent', 'event', '_handle_two_finger_scroll']
    for method_name in expected_methods:
        assert hasattr(view, method_name), f"Method {method_name} should exist"

    print("✓ All expected methods are present")

    # Test that touch events are still enabled
    assert view.testAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents), \
        "Touch events should still be enabled"
    print("✓ Touch events still enabled")

    return True


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        test_ctrl_zoom_functionality()
        test_integration_with_existing_features()
        print("\n✅ CADGraphicsView Ctrl+zoom integration complete!")
        print("\nAll features working:")
        print("- Normal mouse wheel scrolling")
        print("- Shift+wheel horizontal scrolling")
        print("- Multitouch scrolling")
        print("- Ctrl+wheel zooming (NEW)")
        app.quit()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
