#!/usr/bin/env python3
"""Test the Qt preferences dialog integration."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from BelfryCAD.config import AppConfig
from gui.preferences_dialog import PreferencesDialog


class TestMainWindow(QMainWindow):
    """Simple test window to test the preferences dialog."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Qt Preferences Dialog")
        self.setGeometry(100, 100, 400, 200)
        
        # Create config for preferences
        self.config = AppConfig()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create button to open preferences
        prefs_button = QPushButton("Open Preferences")
        prefs_button.clicked.connect(self.show_preferences)
        layout.addWidget(prefs_button)
        
        # Create button to quit
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)
        layout.addWidget(quit_button)
    
    def show_preferences(self):
        """Show the preferences dialog."""
        dialog = PreferencesDialog(self)
        dialog.exec()


def main():
    """Main function to run the test."""
    app = QApplication(sys.argv)
    
    window = TestMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
