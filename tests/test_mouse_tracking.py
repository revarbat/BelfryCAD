#!/usr/bin/env python3
"""
Test script to verify that mouse tracking is working correctly.
This will show a window and print mouse positions as you move the mouse
over the canvas (without requiring any button presses).
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from BelfryCAD.gui.main_window import MainWindow
from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document

def test_mouse_tracking():
    """Test if mouse tracking is working correctly."""
    app = QApplication(sys.argv)
    
    # Create required dependencies
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    
    # Create main window
    main_window = MainWindow(config, preferences, document)
    main_window.show()
    
    print("Mouse tracking test started.")
    print("Move your mouse over the canvas area (without clicking).")
    print("You should see ruler position updates below:")
    print("Press Ctrl+C to exit or the window will close automatically after 30 seconds.")
    print("-" * 60)
    
    # Track mouse position changes
    last_h_pos = None
    last_v_pos = None
    
    def check_ruler_positions():
        nonlocal last_h_pos, last_v_pos
        
        # Get current ruler positions
        h_ruler = main_window.ruler_manager.get_horizontal_ruler()
        v_ruler = main_window.ruler_manager.get_vertical_ruler()
        
        current_h_pos = h_ruler.position
        current_v_pos = v_ruler.position
        
        # Only print if positions have changed
        if current_h_pos != last_h_pos or current_v_pos != last_v_pos:
            print(f"Mouse position: H={current_h_pos:.2f}, V={current_v_pos:.2f}")
            last_h_pos = current_h_pos
            last_v_pos = current_v_pos
    
    # Check ruler positions every 100ms
    timer = QTimer()
    timer.timeout.connect(check_ruler_positions)
    timer.start(100)
    
    # Close after 30 seconds
    QTimer.singleShot(30000, app.quit)
    
    app.exec()

if __name__ == "__main__":
    test_mouse_tracking()
