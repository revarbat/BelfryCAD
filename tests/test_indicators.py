#!/usr/bin/env python3
"""
Test script to check if mouse position indicators are now visible.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QPointF
from BelfryCAD.gui.main_window import MainWindow
from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document

def test_position_indicators():
    """Test if position indicators are visible."""
    app = QApplication(sys.argv)
    
    # Create required dependencies
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    
    # Create main window
    main_window = MainWindow(config, preferences, document)
    main_window.show()
    
    # Test position indicators
    def test_indicators():
        print("Testing position indicator visibility...")
        
        # Get rulers
        h_ruler = main_window.ruler_manager.get_horizontal_ruler()
        v_ruler = main_window.ruler_manager.get_vertical_ruler()
        
        # Test with different scene positions
        test_positions = [
            (0.0, 0.0),      # Center of scene
            (100.0, 50.0),   # Positive quadrant
            (-100.0, -50.0), # Negative quadrant
            (200.0, 200.0),  # Further out
        ]
        
        for x, y in test_positions:
            print(f"\nTesting position ({x}, {y}):")
            
            # Update rulers
            main_window.ruler_manager.update_mouse_position(x, y)
            
            # Check if canvas can map these coordinates
            scene_point_h = main_window.canvas.mapFromScene(x, 0)
            scene_point_v = main_window.canvas.mapFromScene(0, y)
            
            print(f"  Horizontal: scene({x}, 0) -> widget({scene_point_h.x()}, {scene_point_h.y()})")
            print(f"  Vertical: scene(0, {y}) -> widget({scene_point_v.x()}, {scene_point_v.y()})")
            
            # Check bounds
            h_rect = h_ruler.rect()
            v_rect = v_ruler.rect()
            
            h_in_bounds = 0 <= scene_point_h.x() <= h_rect.width()
            v_in_bounds = 0 <= scene_point_v.y() <= v_rect.height()
            
            print(f"  H in bounds: {h_in_bounds} (0 <= {scene_point_h.x()} <= {h_rect.width()})")
            print(f"  V in bounds: {v_in_bounds} (0 <= {scene_point_v.y()} <= {v_rect.height()})")
            
            # Force update
            h_ruler.update()
            v_ruler.update()
    
    # Set up timer to run test after window is shown
    QTimer.singleShot(1000, test_indicators)
    
    # Keep window open longer for visual inspection
    QTimer.singleShot(10000, app.quit)
    
    app.exec()

if __name__ == "__main__":
    test_position_indicators()
