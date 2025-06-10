#!/usr/bin/env python3
"""
Test script to verify that native gesture handling (macOS trackpad) 
would work correctly if native gesture events are received.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QEvent

from BelfryCAD.gui.cad_graphics_view import CADGraphicsView
from BelfryCAD.gui.cad_scene import CadScene
from BelfryCAD.gui.drawing_manager import DrawingManager


def test_native_gesture_handling():
    """Test that the CADGraphicsView handles native gesture events correctly"""
    
    print("🧪 Testing Native Gesture Handling...")
    
    app = QApplication(sys.argv)
    
    # Create CADGraphicsView and dependencies
    view = CADGraphicsView()
    
    # Create mock scene that tracks zoom calls
    mock_scene = Mock(spec=CadScene)
    mock_scene.scale_factor = 1.0
    zoom_calls = []
    
    def track_zoom(scale_factor):
        zoom_calls.append(scale_factor)
        mock_scene.scale_factor = scale_factor
        print(f"  → Native gesture zoom called with scale factor: {scale_factor:.3f}")
    
    mock_scene.set_scale_factor = track_zoom
    
    # Create mock drawing manager
    mock_drawing_manager = Mock(spec=DrawingManager)
    mock_drawing_manager.cad_scene = mock_scene
    view.set_drawing_manager(mock_drawing_manager)
    
    print("✓ Test environment set up")
    
    # Test 1: Create a mock native gesture event (zoom in)
    print("\n  Testing native gesture zoom in...")
    
    mock_event = Mock()
    mock_event.type.return_value = QEvent.Type.NativeGesture
    mock_event.gestureType.return_value = Qt.NativeGestureType.ZoomNativeGesture
    mock_event.value.return_value = 1.2  # 20% zoom in
    mock_event.accept = Mock()
    
    # Test the event handler
    result = view.event(mock_event)
    
    assert result is True, "Native gesture event should be handled"
    assert len(zoom_calls) == 1, "Zoom should have been called once"
    assert zoom_calls[0] == 1.2, f"Expected zoom factor 1.2, got {zoom_calls[0]}"
    assert mock_event.accept.called, "Event should be accepted"
    
    print("✓ Native gesture zoom in works correctly")
    
    # Test 2: Create a mock native gesture event (zoom out)
    print("  Testing native gesture zoom out...")
    
    zoom_calls.clear()
    mock_scene.scale_factor = 1.0
    
    mock_event.value.return_value = 0.8  # 20% zoom out
    mock_event.accept.reset_mock()
    
    result = view.event(mock_event)
    
    assert result is True, "Native gesture event should be handled"
    assert len(zoom_calls) == 1, "Zoom should have been called once"
    assert zoom_calls[0] == 0.8, f"Expected zoom factor 0.8, got {zoom_calls[0]}"
    assert mock_event.accept.called, "Event should be accepted"
    
    print("✓ Native gesture zoom out works correctly")
    
    # Test 3: Test zoom limits with native gestures
    print("  Testing native gesture zoom limits...")
    
    # Test minimum limit
    zoom_calls.clear()
    mock_scene.scale_factor = 0.02  # Near minimum
    mock_event.value.return_value = 0.1  # Extreme zoom out
    
    result = view.event(mock_event)
    
    assert zoom_calls[0] >= 0.01, "Zoom should be clamped to minimum"
    print("    ✓ Minimum zoom limit enforced")
    
    # Test maximum limit
    zoom_calls.clear()
    mock_scene.scale_factor = 95.0  # Near maximum
    mock_event.value.return_value = 2.0  # Extreme zoom in
    
    result = view.event(mock_event)
    
    assert zoom_calls[0] <= 100.0, "Zoom should be clamped to maximum"
    print("    ✓ Maximum zoom limit enforced")
    
    # Test 4: Test non-zoom native gestures are ignored
    print("  Testing non-zoom native gestures are ignored...")
    
    zoom_calls.clear()
    mock_event.gestureType.return_value = Qt.NativeGestureType.PanNativeGesture
    mock_event.accept.reset_mock()
    
    result = view.event(mock_event)
    
    # Should fall through to parent event handler
    assert len(zoom_calls) == 0, "Pan gesture should not trigger zoom"
    print("    ✓ Non-zoom gestures are ignored")
    
    print("\n🎉 All native gesture tests passed!")
    print("\nNative gesture features verified:")
    print("- ZoomNativeGesture detection and handling")
    print("- Proper zoom factor application")
    print("- Zoom limit enforcement (0.01x to 100x)")
    print("- Event acceptance for handled gestures")
    print("- Non-zoom gesture filtering")
    
    app.quit()
    return True


if __name__ == "__main__":
    try:
        test_native_gesture_handling()
        print("\n✅ Native gesture handling verification complete!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
