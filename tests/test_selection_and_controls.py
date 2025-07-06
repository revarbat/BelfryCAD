#!/usr/bin/env python3
"""
Test script for selection and control point system.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# Add the BelfryCAD directory to the path
sys.path.insert(0, 'BelfryCAD')

from ..src.BelfryCAD.gui.widgets.cad_scene import CadScene
from ..src.BelfryCAD.gui.widgets.cad_view import CadView
from ..src.BelfryCAD.gui.graphics_items.caditems.line_cad_item import LineCadItem
from ..src.BelfryCAD.gui.graphics_items.caditems.rectangle_cad_item import RectangleCadItem
from ..src.BelfryCAD.gui.graphics_items.caditems.circle_center_radius_cad_item import CircleCenterRadiusCadItem


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selection and Controls Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create scene and view
        self.scene = CadScene()
        self.view = CadView(self.scene)
        layout.addWidget(self.view)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        
        add_line_btn = QPushButton("Add Line")
        add_line_btn.clicked.connect(self.add_line)
        button_layout.addWidget(add_line_btn)
        
        add_rect_btn = QPushButton("Add Rectangle")
        add_rect_btn.clicked.connect(self.add_rectangle)
        button_layout.addWidget(add_rect_btn)
        
        add_circle_btn = QPushButton("Add Circle")
        add_circle_btn.clicked.connect(self.add_circle)
        button_layout.addWidget(add_circle_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        # Add some test items
        self.add_line()
        self.add_rectangle()
        self.add_circle()
        
        # Instructions
        instructions = """
        Selection Test Instructions:
        1. Click on items to select them individually
        2. Hold Shift and click to add items to selection
        3. Hold Command (Ctrl) and click to toggle selection
        4. When exactly one item is selected, control points should appear
        5. Drag control points to modify the item geometry
        6. Click on control datums (if any) to edit values
        """
        print(instructions)

    def add_line(self):
        """Add a line to the scene."""
        line = LineCadItem(
            start_point=(0, 0),
            end_point=(2, 1),
            color=QColor(255, 0, 0)
        )
        self.scene.addItem(line)

    def add_rectangle(self):
        """Add a rectangle to the scene."""
        rect = RectangleCadItem(
            top_left=(2, 1.5),
            top_right=(4, 1.5),
            bottom_right=(4, 0),
            bottom_left=(2, 0),
            color=QColor(0, 255, 0)
        )
        self.scene.addItem(rect)

    def add_circle(self):
        """Add a circle to the scene."""
        circle = CircleCenterRadiusCadItem(
            center_point=(0, 3),
            perimeter_point=(1, 3),
            color=QColor(0, 0, 255)
        )
        self.scene.addItem(circle)

    def clear_all(self):
        """Clear all items from the scene."""
        self.scene.clear()


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 