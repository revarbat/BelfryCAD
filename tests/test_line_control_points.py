#!/usr/bin/env python3
"""
Test script to verify LineCadItem control points are positioned correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPen, QColor

from ..src.BelfryCAD.gui.views.widgets.cad_scene import CadScene
from ..src.BelfryCAD.gui.views.widgets.cad_view import CadView
from ..src.BelfryCAD.gui.views.graphics_items.caditems.line_cad_item import LineCadItem


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Line Control Points Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create scene and view
        self.scene = CadScene()
        self.view = CadView(self.scene)
        layout.addWidget(self.view)
        
        # Create a line for testing
        self.create_test_line()
        
        print("Line Control Points Test Window Created")
        print("Instructions:")
        print("1. Click on the line to select it")
        print("2. Control points should appear at the start, end, and midpoint")
        print("3. Try dragging control points to modify the line")

    def create_test_line(self):
        """Create a test line with reasonable coordinates."""
        # Create a line from (1,1) to (4,3) in inches
        start_point = QPointF(1.0, 1.0)
        end_point = QPointF(4.0, 3.0)
        
        # Create the line
        self.line = LineCadItem(
            start_point=start_point, 
            end_point=end_point, 
            color=QColor(255, 0, 0), 
            line_width=0.05
        )
        
        # Add to scene
        self.scene.addItem(self.line)
        
        print(f"Created line from {start_point} to {end_point}")
        print(f"Line bounds: {self.line.boundingRect()}")


def main():
    app = QApplication(sys.argv)
    
    # Create and show the test window
    window = TestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 