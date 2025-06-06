#!/usr/bin/env python3
"""
Test script to check mouse position indicators in rulers.
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

def test_mouse_position():
    """Test the mouse position indicators."""
    app = QApplication(sys.argv)

    # Create required dependencies
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()

    # Create main window
    main_window = MainWindow(config, preferences, document)
    main_window.show()

    # Test mouse position updates manually
    def test_positions():
        print("Testing mouse position updates...")

        # Get rulers
        h_ruler = main_window.ruler_manager.get_horizontal_ruler()
        v_ruler = main_window.ruler_manager.get_vertical_ruler()

        print(f"Initial horizontal ruler position: {h_ruler.position}")
        print(f"Initial vertical ruler position: {v_ruler.position}")

        # Update positions manually
        main_window.ruler_manager.update_mouse_position(50.0, 25.0)
        print(f"After update (50, 25) - H: {h_ruler.position}, V: {v_ruler.position}")

        main_window.ruler_manager.update_mouse_position(100.0, 75.0)
        print(f"After update (100, 75) - H: {h_ruler.position}, V: {v_ruler.position}")

        # Test that rulers are updating visually
        h_ruler.update()
        v_ruler.update()
        print("Rulers updated visually")

    # Set up timer to run test after window is shown
    QTimer.singleShot(1000, test_positions)

    # Run for a short time then exit
    QTimer.singleShot(3000, app.quit)

    app.exec()

if __name__ == "__main__":
    test_mouse_position()
