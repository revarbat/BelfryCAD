#!/usr/bin/env python3
"""
Visual test for rulers in PyTkCAD - opens the application with rulers visible.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QPointF
from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document
from BelfryCAD.gui.main_window import MainWindow


def visual_test_rulers():
    """Visual test to demonstrate rulers functionality."""
    app = QApplication([])
    
    # Create application components
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    
    # Create main window
    main_window = MainWindow(config, preferences, document)
    main_window.show()
    
    print("PyTkCAD opened with rulers!")
    print("You should see:")
    print("- Horizontal ruler at the top")
    print("- Vertical ruler on the left")
    print("- A white corner square in the top-left")
    print("- Canvas taking up the remaining space")
    print("")
    print("Test the rulers by:")
    print("1. Moving your mouse around - rulers should show position indicators")
    print("2. Scrolling the canvas - rulers should update to show visible area")
    print("3. Using drawing tools - rulers help with precise positioning")
    print("")
    print("Close the window to exit the test.")
    
    # Keep the application running until user closes it
    sys.exit(app.exec())


if __name__ == "__main__":
    visual_test_rulers()
