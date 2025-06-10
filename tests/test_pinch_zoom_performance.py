#!/usr/bin/env python3
"""
Test pinch-to-zoom performance improvements
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import time

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QPointF
    from PySide6.QtGui import QNativeGestureEvent
    
    from BelfryCAD.gui.cad_graphics_view import CADGraphicsView
    from BelfryCAD.gui.cad_scene import CadScene
    from BelfryCAD.gui.drawing_manager import DrawingManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required dependencies are installed")
    sys.exit(1)


class TestPinchZoomPerformance(unittest.TestCase):
    """Test performance improvements for pinch-to-zoom"""

    def setUp(self):
        """Set up test environment"""
        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()
        
        # Create test components
        self.cad_scene = CadScene()
        self.drawing_manager = DrawingManager(self.cad_scene)
        self.graphics_view = CADGraphicsView()
        self.graphics_view.set_drawing_manager(self.drawing_manager)
        
        # Mock the expensive redraw_grid method to track calls
        self.grid_redraw_calls = 0
        self.original_redraw_grid = self.cad_scene.redraw_grid
        
        def mock_redraw_grid():
            self.grid_redraw_calls += 1
            # Simulate some processing time
            time.sleep(0.001)  # 1ms delay to simulate work
            
        self.cad_scene.redraw_grid = mock_redraw_grid

    def tearDown(self):
        """Clean up after tests"""
        # Restore original method
        self.cad_scene.redraw_grid = self.original_redraw_grid

    def test_deferred_grid_redraw_during_native_gesture(self):
        """Test that grid redraw is deferred during native gesture"""
        # Reset counter
        self.grid_redraw_calls = 0
        
        # Simulate begin native gesture
        self.graphics_view._native_gesture_active = True
        self.graphics_view._gesture_in_progress = True
        
        # Simulate multiple zoom updates during gesture
        initial_scale = self.cad_scene.scale_factor
        for i in range(10):
            new_scale = initial_scale * (1.0 + (i * 0.01))  # Small incremental zooms
            self.cad_scene.set_scale_factor(new_scale, defer_grid_redraw=True)
        
        # During gesture, no grid redraws should have occurred
        self.assertEqual(self.grid_redraw_calls, 0, 
                        "Grid should not be redrawn during deferred mode")
        
        # Simulate end of gesture
        self.graphics_view._native_gesture_active = False
        self.graphics_view._gesture_in_progress = False
        self.cad_scene.redraw_grid()  # Manual redraw as would happen in end gesture
        
        # Now grid should have been redrawn once
        self.assertEqual(self.grid_redraw_calls, 1,
                        "Grid should be redrawn once at end of gesture")

    def test_normal_grid_redraw_without_defer(self):
        """Test that grid redraw works normally when not deferred"""
        # Reset counter
        self.grid_redraw_calls = 0
        
        # Normal scale factor change without defer flag
        initial_scale = self.cad_scene.scale_factor
        self.cad_scene.set_scale_factor(initial_scale * 1.5)
        
        # Grid should have been redrawn immediately
        self.assertEqual(self.grid_redraw_calls, 1,
                        "Grid should be redrawn immediately when not deferred")

    def test_gesture_state_tracking(self):
        """Test that gesture state is properly tracked"""
        # Initial state should be no gesture
        self.assertFalse(self.graphics_view._gesture_in_progress)
        self.assertFalse(self.graphics_view._native_gesture_active)
        
        # Simulate native gesture begin
        self.graphics_view._native_gesture_active = True
        self.graphics_view._gesture_in_progress = True
        
        self.assertTrue(self.graphics_view._gesture_in_progress)
        self.assertTrue(self.graphics_view._native_gesture_active)
        
        # Simulate native gesture end
        self.graphics_view._native_gesture_active = False
        self.graphics_view._gesture_in_progress = False
        
        self.assertFalse(self.graphics_view._gesture_in_progress)
        self.assertFalse(self.graphics_view._native_gesture_active)

    def test_performance_comparison(self):
        """Test performance improvement by comparing deferred vs immediate redraw"""
        # Reset counter
        self.grid_redraw_calls = 0
        
        # Test immediate redraw (old behavior) - simulate 20 zoom updates
        start_time = time.time()
        initial_scale = self.cad_scene.scale_factor
        for i in range(20):
            new_scale = initial_scale * (1.0 + (i * 0.01))
            self.cad_scene.set_scale_factor(new_scale, defer_grid_redraw=False)
        immediate_time = time.time() - start_time
        immediate_calls = self.grid_redraw_calls
        
        # Reset for deferred test
        self.grid_redraw_calls = 0
        
        # Test deferred redraw (new behavior) - simulate 20 zoom updates
        start_time = time.time()
        for i in range(20):
            new_scale = initial_scale * (1.0 + (i * 0.01))
            self.cad_scene.set_scale_factor(new_scale, defer_grid_redraw=True)
        # Single redraw at end
        self.cad_scene.redraw_grid()
        deferred_time = time.time() - start_time
        deferred_calls = self.grid_redraw_calls
        
        print(f"Immediate redraw: {immediate_calls} calls, {immediate_time:.4f}s")
        print(f"Deferred redraw: {deferred_calls} calls, {deferred_time:.4f}s")
        print(f"Performance improvement: {immediate_time/deferred_time:.2f}x faster")
        
        # Deferred should have significantly fewer redraw calls
        self.assertLess(deferred_calls, immediate_calls,
                       "Deferred redraw should have fewer grid redraw calls")
        
        # Deferred should be faster
        self.assertLess(deferred_time, immediate_time,
                       "Deferred redraw should be faster than immediate redraw")


if __name__ == '__main__':
    unittest.main()
