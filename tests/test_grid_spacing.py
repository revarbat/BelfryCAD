#!/usr/bin/env python3
"""
Test script to verify grid spacing matches ruler major tickmarks
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt
from BelfryCAD.gui.main_window import CADGraphicsView
from BelfryCAD.gui.rulers import RulerManager
from PySide6.QtWidgets import QGraphicsScene

class GridTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Spacing Test")
        self.resize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create scene and canvas
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-50, -50, 100, 100)
        
        self.canvas = CADGraphicsView()
        self.canvas.setScene(self.scene)
        
        # Create rulers
        self.ruler_manager = RulerManager(self.canvas, central_widget)
        h_ruler = self.ruler_manager.get_horizontal_ruler()
        v_ruler = self.ruler_manager.get_vertical_ruler()
        
        # Corner widget
        corner = QWidget()
        corner.setFixedSize(32, 32)
        corner.setStyleSheet("background-color: white; border: 1px solid black;")
        
        # Layout
        layout.addWidget(corner, 0, 0)
        layout.addWidget(h_ruler, 0, 1)
        layout.addWidget(v_ruler, 1, 0)
        layout.addWidget(self.canvas, 1, 1)
        
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)
        
        # Add grid and test objects
        self._add_grid()
        self._add_test_objects()
    
    def _add_grid(self):
        """Add grid lines using same logic as main window"""
        # Get grid info
        h_ruler = self.ruler_manager.get_horizontal_ruler()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = h_ruler.get_grid_info()
        
        # Use the same improved grid spacing as main window
        grid_spacing = majorspacing * 5  # Every 5 units for less dense grid
        
        print(f"Grid info: labelspacing={labelspacing}, majorspacing={majorspacing}")
        print(f"Using grid_spacing={grid_spacing} for less dense grid")
        
        # Create grid pen
        grid_pen = QPen(QColor(200, 200, 200))
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DotLine)
        
        scene_rect = self.scene.sceneRect()
        
        # Vertical grid lines
        import math
        x_start = scene_rect.left()
        x_end = scene_rect.right()
        first_x = math.floor(x_start / grid_spacing) * grid_spacing
        
        print(f"Drawing vertical lines from {first_x} to {x_end} with spacing {grid_spacing}")
        
        x = first_x
        count = 0
        while x <= x_end and count < 10:  # Limit for debugging
            grid_line = self.scene.addLine(
                x, scene_rect.top(), x, scene_rect.bottom(), grid_pen
            )
            grid_line.setZValue(-1001)
            print(f"  Vertical line at x={x}")
            x += grid_spacing
            count += 1
        
        # Horizontal grid lines
        y_start = scene_rect.top()
        y_end = scene_rect.bottom()
        first_y = math.floor(y_start / grid_spacing) * grid_spacing
        
        print(f"Drawing horizontal lines from {first_y} to {y_end} with spacing {grid_spacing}")
        
        y = first_y
        count = 0
        while y <= y_end and count < 10:  # Limit for debugging
            grid_line = self.scene.addLine(
                scene_rect.left(), y, scene_rect.right(), y, grid_pen
            )
            grid_line.setZValue(-1001)
            print(f"  Horizontal line at y={y}")
            y += grid_spacing
            count += 1
    
    def _add_test_objects(self):
        """Add some test objects to verify grid alignment"""
        # Add axis lines
        axis_pen = QPen(QColor(128, 128, 128))
        axis_pen.setWidth(2)
        
        scene_rect = self.scene.sceneRect()
        
        # Horizontal axis (y=0)
        h_axis = self.scene.addLine(
            scene_rect.left(), 0, scene_rect.right(), 0, axis_pen
        )
        h_axis.setZValue(-1000)
        
        # Vertical axis (x=0) 
        v_axis = self.scene.addLine(
            0, scene_rect.top(), 0, scene_rect.bottom(), axis_pen
        )
        v_axis.setZValue(-1000)
        
        # Add some test shapes at grid positions
        test_pen = QPen(QColor(255, 0, 0))
        test_pen.setWidth(2)
        
        # Rectangle from (1,1) to (3,2) - should align with grid
        self.scene.addRect(1, 1, 2, 1, test_pen)
        
        # Circle at (5, 3) with radius 1
        self.scene.addEllipse(4, 2, 2, 2, test_pen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GridTestWindow()
    window.show()
    sys.exit(app.exec())
