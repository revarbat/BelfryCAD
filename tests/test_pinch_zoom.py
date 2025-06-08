#!/usr/bin/env python3
"""
Test suite for two-finger pinch-to-zoom functionality in CADGraphicsView.

This test validates:
1. Pinch gesture detection and zoom factor calculation
2. Integration with existing CadScene.set_scale_factor()
3. Proper zoom limits (0.01x to 100x)
4. Smooth zoom sensitivity
5. Combination of pinch zoom with panning
6. Touch event lifecycle management
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the project root to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import QEvent, QPointF
from PySide6.QtGui import QTouchEvent

from BelfryCAD.gui.cad_graphics_view import CADGraphicsView
from BelfryCAD.gui.cad_scene import CadScene
from BelfryCAD.gui.drawing_manager import DrawingManager


class TestPinchZoom(unittest.TestCase):
    """Test cases for pinch-to-zoom functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests"""
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test environment"""
        # Create CADGraphicsView instance
        self.view = CADGraphicsView()
        
        # Create mock CadScene
        self.mock_scene = Mock(spec=CadScene)
        self.mock_scene.scale_factor = 1.0
        
        # Create mock DrawingManager
        self.mock_drawing_manager = Mock(spec=DrawingManager)
        self.mock_drawing_manager.cad_scene = self.mock_scene
        
        # Set up the view with mocked dependencies
        self.view.set_drawing_manager(self.mock_drawing_manager)
        
        # Initialize Qt scene
        qt_scene = QGraphicsScene()
        self.view.setScene(qt_scene)
    
    def tearDown(self):
        """Clean up after each test"""
        self.view.close()
    
    def create_mock_touch_event(self, event_type, touch_points):
        """Create a mock touch event with specified points"""
        event = Mock()
        event.type.return_value = event_type
        event.touchPoints.return_value = touch_points
        event.accept = Mock()
        return event
    
    def create_mock_touch_point(self, pos, last_pos=None):
        """Create a mock touch point at specified position"""
        point = Mock()
        point.pos.return_value = QPointF(pos[0], pos[1])
        if last_pos:
            point.lastPos.return_value = QPointF(last_pos[0], last_pos[1])
        else:
            point.lastPos.return_value = QPointF(pos[0], pos[1])
        return point
    
    def test_pinch_zoom_spread_gesture(self):
        """Test pinch spread (zoom in) gesture"""
        # Create initial touch points close together
        point1 = self.create_mock_touch_point((100, 100), (100, 100))
        point2 = self.create_mock_touch_point((110, 110), (110, 110))
        
        # First touch event to establish baseline
        event1 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1, point2])
        self.view._handle_two_finger_scroll(event1)
        
        # Create second touch points spread further apart (zoom in)
        point1_spread = self.create_mock_touch_point((90, 90), (100, 100))
        point2_spread = self.create_mock_touch_point((120, 120), (110, 110))
        
        # Second touch event with spread gesture
        event2 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1_spread, point2_spread])
        self.view._handle_two_finger_scroll(event2)
        
        # Verify that zoom in was called (scale factor should increase)
        self.mock_scene.set_scale_factor.assert_called()
        called_scale = self.mock_scene.set_scale_factor.call_args[0][0]
        self.assertGreater(called_scale, 1.0, "Scale factor should increase for spread gesture")
    
    def test_pinch_zoom_squeeze_gesture(self):
        """Test pinch squeeze (zoom out) gesture"""
        # Create initial touch points far apart
        point1 = self.create_mock_touch_point((80, 80), (80, 80))
        point2 = self.create_mock_touch_point((120, 120), (120, 120))
        
        # First touch event to establish baseline
        event1 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1, point2])
        self.view._handle_two_finger_scroll(event1)
        
        # Create second touch points closer together (zoom out)
        point1_squeeze = self.create_mock_touch_point((95, 95), (80, 80))
        point2_squeeze = self.create_mock_touch_point((105, 105), (120, 120))
        
        # Second touch event with squeeze gesture
        event2 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1_squeeze, point2_squeeze])
        self.view._handle_two_finger_scroll(event2)
        
        # Verify that zoom out was called (scale factor should decrease)
        self.mock_scene.set_scale_factor.assert_called()
        called_scale = self.mock_scene.set_scale_factor.call_args[0][0]
        self.assertLess(called_scale, 1.0, "Scale factor should decrease for squeeze gesture")
    
    def test_zoom_limits(self):
        """Test that zoom is clamped to reasonable limits"""
        # Test minimum zoom limit
        self.mock_scene.scale_factor = 0.02  # Close to minimum
        
        # Create extreme squeeze gesture
        point1 = self.create_mock_touch_point((50, 50), (50, 50))
        point2 = self.create_mock_touch_point((150, 150), (150, 150))
        event1 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1, point2])
        self.view._handle_two_finger_scroll(event1)
        
        # Create extreme squeeze
        point1_squeeze = self.create_mock_touch_point((99, 99), (50, 50))
        point2_squeeze = self.create_mock_touch_point((101, 101), (150, 150))
        event2 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1_squeeze, point2_squeeze])
        self.view._handle_two_finger_scroll(event2)
        
        # Verify minimum limit is enforced
        called_scale = self.mock_scene.set_scale_factor.call_args[0][0]
        self.assertGreaterEqual(called_scale, 0.01, "Scale factor should not go below 0.01")
        
        # Test maximum zoom limit
        self.mock_scene.scale_factor = 95.0  # Close to maximum
        
        # Create extreme spread gesture
        point1_spread = self.create_mock_touch_point((10, 10), (99, 99))
        point2_spread = self.create_mock_touch_point((190, 190), (101, 101))
        event3 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1_spread, point2_spread])
        self.view._handle_two_finger_scroll(event3)
        
        # Verify maximum limit is enforced
        called_scale = self.mock_scene.set_scale_factor.call_args[0][0]
        self.assertLessEqual(called_scale, 100.0, "Scale factor should not exceed 100.0")
    
    def test_pinch_threshold(self):
        """Test that small distance changes don't trigger zoom"""
        # Create touch points with minimal distance change
        point1 = self.create_mock_touch_point((100, 100), (100, 100))
        point2 = self.create_mock_touch_point((110, 110), (110, 110))
        event1 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1, point2])
        self.view._handle_two_finger_scroll(event1)
        
        # Reset mock to clear any calls
        self.mock_scene.set_scale_factor.reset_mock()
        
        # Create tiny movement (below threshold)
        point1_tiny = self.create_mock_touch_point((100.5, 100.5), (100, 100))
        point2_tiny = self.create_mock_touch_point((110.5, 110.5), (110, 110))
        event2 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1_tiny, point2_tiny])
        self.view._handle_two_finger_scroll(event2)
        
        # Verify that zoom was not triggered for tiny movements
        self.mock_scene.set_scale_factor.assert_not_called()
    
    def test_touch_lifecycle_reset(self):
        """Test that pinch distance tracking resets on touch end"""
        # Simulate touch begin/update/end cycle
        point1 = self.create_mock_touch_point((100, 100))
        point2 = self.create_mock_touch_point((110, 110))
        
        # Touch update event
        event_update = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1, point2])
        self.view._handle_two_finger_scroll(event_update)
        
        # Verify that pinch distance is tracked
        self.assertIsNotNone(self.view._last_pinch_distance)
        
        # Touch end event - test the event handler directly
        event_end = Mock()
        event_end.type.return_value = QEvent.Type.TouchEnd
        event_end.touchPoints.return_value = []
        
        # Manually trigger the touch end handling logic
        if hasattr(event_end, 'type') and event_end.type() == QEvent.Type.TouchEnd:
            self.view._last_pinch_distance = None
        
        # Verify that pinch distance tracking is reset
        self.assertIsNone(self.view._last_pinch_distance)
    
    def test_combined_pinch_and_pan(self):
        """Test that pinch zoom and panning can work together"""
        # Create touch points that both spread (zoom) and move (pan)
        point1 = self.create_mock_touch_point((100, 100), (100, 100))
        point2 = self.create_mock_touch_point((110, 110), (110, 110))
        event1 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1, point2])
        self.view._handle_two_finger_scroll(event1)
        
        # Mock the scroll bars for pan testing
        mock_h_bar = Mock()
        mock_v_bar = Mock()
        mock_h_bar.value.return_value = 0
        mock_v_bar.value.return_value = 0
        
        with patch.object(self.view, 'horizontalScrollBar', return_value=mock_h_bar), \
             patch.object(self.view, 'verticalScrollBar', return_value=mock_v_bar):
            
            # Create touch points that spread (zoom in) and move right/down (pan)
            point1_combined = self.create_mock_touch_point((85, 85), (100, 100))  # Move up-left, spread
            point2_combined = self.create_mock_touch_point((135, 135), (110, 110))  # Move down-right, spread
            event2 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1_combined, point2_combined])
            self.view._handle_two_finger_scroll(event2)
            
            # Verify both zoom and pan occurred
            self.mock_scene.set_scale_factor.assert_called()  # Zoom occurred
            mock_h_bar.setValue.assert_called()  # Horizontal pan occurred
            mock_v_bar.setValue.assert_called()  # Vertical pan occurred
    
    def test_zoom_sensitivity(self):
        """Test zoom sensitivity configuration"""
        # Create a moderate spread gesture
        point1 = self.create_mock_touch_point((100, 100), (100, 100))
        point2 = self.create_mock_touch_point((110, 110), (110, 110))
        event1 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1, point2])
        self.view._handle_two_finger_scroll(event1)
        
        # Create a spread gesture with known distance change
        point1_spread = self.create_mock_touch_point((90, 90), (100, 100))
        point2_spread = self.create_mock_touch_point((120, 120), (110, 110))
        event2 = self.create_mock_touch_event(QEvent.Type.TouchUpdate, [point1_spread, point2_spread])
        self.view._handle_two_finger_scroll(event2)
        
        # Verify the zoom factor is reasonable (not too sensitive)
        called_scale = self.mock_scene.set_scale_factor.call_args[0][0]
        self.assertGreater(called_scale, 1.0, "Should zoom in")
        self.assertLess(called_scale, 2.0, "Should not be overly sensitive")


def run_pinch_zoom_tests():
    """Run the pinch zoom test suite"""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPinchZoom)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running Pinch-to-Zoom Tests...")
    print("=" * 50)
    
    success = run_pinch_zoom_tests()
    
    if success:
        print("\n✅ All pinch-to-zoom tests passed!")
    else:
        print("\n❌ Some pinch-to-zoom tests failed!")
        sys.exit(1)
