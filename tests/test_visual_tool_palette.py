#!/usr/bin/env python3
"""
Quick visual test to check tool palette icons are visible
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document
from BelfryCAD.gui.main_window import MainWindow

def main():
    """Create a simple test to verify tool palette icons are visible"""
    app = QApplication([])

    # Create required dependencies
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()

    # Create main window
    window = MainWindow(config, preferences, document)
    window.show()

    print("✓ Application started successfully")
    print("✓ Tool palette should be visible on the left side")
    print("✓ Icons should be displayed in the toolbar")
    print("✓ Press and hold any tool button to see tool palette")
    print("✓ Close the window to exit")

    # Run the application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
