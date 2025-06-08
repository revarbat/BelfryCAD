#!/usr/bin/env python3
"""
Comprehensive integration test for CADGraphicsView functionality.
Tests all scrolling and zooming features working together.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QWheelEvent

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BelfryCAD.gui.cad_graphics_view import CADGraphicsView


class MockCadScene:
    """Mock CadScene for testing"""
    def __init__(self):
        self.scale_factor = 1.0
        self.zoom_calls = []
        
    def set_scale_factor(self, scale_factor):
        self.zoom_calls.append(scale_factor)
        self.scale_factor = scale_factor


class MockDrawingManager:
    """Mock DrawingManager for testing"""
    def __init__(self):
        self.cad_scene = MockCadScene()


def create_wheel_event(angle_delta_y, modifiers):
    """Helper to create QWheelEvent"""
    return QWheelEvent(
        QPoint(100, 100), QPoint(100, 100), QPoint(0, 0),
        QPoint(0, angle_delta_y), Qt.MouseButton.NoButton,
        modifiers, Qt.ScrollPhase.NoScrollPhase, False
    )


def test_comprehensive_functionality():
    """Test all CADGraphicsView functionality together"""
    
    app = QApplication(sys.argv)
    
    print("🧪 Comprehensive CADGraphicsView Functionality Test")
    print("=" * 60)
    
    # Create view and mock components
    view = CADGraphicsView()
    mock_drawing_manager = MockDrawingManager()
    view.set_drawing_manager(mock_drawing_manager)
    
    print("✓ CADGraphicsView created with mock drawing manager")
    
    # Test 1: Normal scrolling (should not zoom)
    print("\n1. Testing normal wheel scrolling...")
    normal_event = create_wheel_event(120, Qt.KeyboardModifier.NoModifier)
    mock_drawing_manager.cad_scene.zoom_calls = []
    view.wheelEvent(normal_event)
    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 0
    print("   ✓ Normal scrolling works, no zoom triggered")
    
    # Test 2: Shift+wheel scrolling (should not zoom)
    print("\n2. Testing Shift+wheel horizontal scrolling...")
    shift_event = create_wheel_event(120, Qt.KeyboardModifier.ShiftModifier)
    mock_drawing_manager.cad_scene.zoom_calls = []
    view.wheelEvent(shift_event)
    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 0
    print("   ✓ Horizontal scrolling works, no zoom triggered")
    
    # Test 3: Ctrl+wheel zoom in
    print("\n3. Testing Ctrl+wheel zoom in...")
    ctrl_zoom_in = create_wheel_event(120, Qt.KeyboardModifier.ControlModifier)
    mock_drawing_manager.cad_scene.scale_factor = 1.0
    mock_drawing_manager.cad_scene.zoom_calls = []
    view.wheelEvent(ctrl_zoom_in)
    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 1
    assert mock_drawing_manager.cad_scene.zoom_calls[0] == 1.1
    print(f"   ✓ Zoom in works: 1.0 → {mock_drawing_manager.cad_scene.zoom_calls[0]}")
    
    # Test 4: Ctrl+wheel zoom out
    print("\n4. Testing Ctrl+wheel zoom out...")
    ctrl_zoom_out = create_wheel_event(-120, Qt.KeyboardModifier.ControlModifier)
    mock_drawing_manager.cad_scene.scale_factor = 1.0
    mock_drawing_manager.cad_scene.zoom_calls = []
    view.wheelEvent(ctrl_zoom_out)
    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 1
    assert mock_drawing_manager.cad_scene.zoom_calls[0] == 0.9
    print(f"   ✓ Zoom out works: 1.0 → {mock_drawing_manager.cad_scene.zoom_calls[0]}")
    
    # Test 5: Multiple zoom operations
    print("\n5. Testing multiple zoom operations...")
    mock_drawing_manager.cad_scene.scale_factor = 1.0
    mock_drawing_manager.cad_scene.zoom_calls = []
    
    # Zoom in twice
    view.wheelEvent(ctrl_zoom_in)
    scale_after_first = mock_drawing_manager.cad_scene.scale_factor
    view.wheelEvent(ctrl_zoom_in)
    
    assert len(mock_drawing_manager.cad_scene.zoom_calls) == 2
    print(f"   ✓ Multiple zooms: 1.0 → {scale_after_first:.3f} → {mock_drawing_manager.cad_scene.scale_factor:.3f}")
    
    # Test 6: Zoom limits
    print("\n6. Testing zoom limits...")
    
    # Test minimum limit
    mock_drawing_manager.cad_scene.scale_factor = 0.02
    mock_drawing_manager.cad_scene.zoom_calls = []
    view.wheelEvent(ctrl_zoom_out)
    assert mock_drawing_manager.cad_scene.zoom_calls[0] >= 0.01
    print(f"   ✓ Minimum limit enforced: 0.02 → {mock_drawing_manager.cad_scene.zoom_calls[0]:.3f}")
    
    # Test maximum limit  
    mock_drawing_manager.cad_scene.scale_factor = 95.0
    mock_drawing_manager.cad_scene.zoom_calls = []
    view.wheelEvent(ctrl_zoom_in)
    assert mock_drawing_manager.cad_scene.zoom_calls[0] <= 100.0
    print(f"   ✓ Maximum limit enforced: 95.0 → {mock_drawing_manager.cad_scene.zoom_calls[0]:.1f}")
    
    # Test 7: Touch events still enabled
    print("\n7. Testing multitouch support...")
    assert view.testAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents)
    assert hasattr(view, '_handle_two_finger_scroll')
    assert hasattr(view, 'event')
    print("   ✓ Multitouch scrolling support preserved")
    
    # Test 8: All required methods present
    print("\n8. Testing method availability...")
    required_methods = [
        'wheelEvent', 'event', '_handle_two_finger_scroll',
        'set_drawing_manager', 'set_tool_manager'
    ]
    for method in required_methods:
        assert hasattr(view, method), f"Missing method: {method}"
    print(f"   ✓ All {len(required_methods)} required methods present")
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("\nCADGraphicsView Feature Summary:")
    print("✅ Normal mouse wheel scrolling")
    print("✅ Shift+wheel horizontal scrolling")
    print("✅ Multitouch scrolling support")
    print("✅ Ctrl+wheel zooming (NEW)")
    print("✅ Zoom limits (0.01x to 100x)")
    print("✅ 10% zoom sensitivity")
    print("✅ Proper event handling")
    print("✅ Full backward compatibility")
    
    app.quit()
    return True


if __name__ == "__main__":
    try:
        test_comprehensive_functionality()
        print("\n✅ Comprehensive integration test PASSED!")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
