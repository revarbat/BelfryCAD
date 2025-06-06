#!/usr/bin/env python3
"""
Verification script to demonstrate PNG icon scaling functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from BelfryCAD.gui.main_window import MainWindow
from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document

def create_verification_window():
    """Create a window showing before/after comparison of PNG icons"""
    
    # Create the necessary dependencies for MainWindow
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    
    # Create a main window instance to access the icon loading method
    main_window = MainWindow(config, preferences, document)
    
    # Create verification window
    verification_window = QMainWindow()
    verification_window.setWindowTitle("PNG Icon Scaling Verification")
    verification_window.resize(800, 400)
    
    central_widget = QWidget()
    layout = QVBoxLayout()
    
    # Test icons that should be PNG only (no SVG version)
    test_icons = ['tool-point', 'tool-rectangle', 'tool-text']
    
    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    
    for icon_name in test_icons:
        png_path = os.path.join(images_dir, f"{icon_name}.png")
        
        if os.path.exists(png_path):
            # Load original PNG (32x32)
            original_pixmap = QPixmap(png_path)
            original_label = QLabel(f"Original {icon_name}: {original_pixmap.width()}x{original_pixmap.height()}")
            original_label.setPixmap(original_pixmap)
            layout.addWidget(original_label)
            
            # Load scaled PNG using MainWindow method (should be 48x48)
            scaled_icon = main_window._load_tool_icon(icon_name)
            if scaled_icon and not scaled_icon.isNull():
                scaled_pixmap = scaled_icon.pixmap(48, 48)
                scaled_label = QLabel(f"Scaled {icon_name}: {scaled_pixmap.width()}x{scaled_pixmap.height()} (150%)")
                scaled_label.setPixmap(scaled_pixmap)
                layout.addWidget(scaled_label)
            
            # Add separator
            separator = QLabel("─" * 50)
            layout.addWidget(separator)
    
    central_widget.setLayout(layout)
    verification_window.setCentralWidget(central_widget)
    
    return verification_window

def main():
    app = QApplication(sys.argv)
    
    print("Creating PNG scaling verification window...")
    verification_window = create_verification_window()
    verification_window.show()
    
    print("PNG Scaling Verification:")
    print("- Original icons should be 32x32 pixels")
    print("- Scaled icons should be 48x48 pixels (150% of original)")
    print("- Visual comparison window opened")
    
    # Don't start event loop, just show verification info
    # app.exec()

if __name__ == "__main__":
    main()
