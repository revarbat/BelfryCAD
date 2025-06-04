#!/usr/bin/env python3
"""
Test the final grid implementation with some test shapes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtCore import Qt
from src.gui.main_window import CADGraphicsView
from src.gui.rulers import RulerManager
from PySide6.QtWidgets import QGraphicsScene

class FinalGridTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Final Grid Test - Reasonable Spacing")
        self.resize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create scene and canvas (smaller scene for better view)
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-25, -25, 50, 50)
        
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
        
        print("Final grid test created with:")
        print("- Grid lines every 5 units (not too dense)")
        print("- Test shapes at grid-aligned positions")
        print("- Axis lines at x=0, y=0")
    
    def _add_grid(self):
        """Add grid using the final improved spacing"""
        # Get grid info
        h_ruler = self.ruler_manager.get_horizontal_ruler()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = h_ruler.get_grid_info()
        
        # Use improved spacing: majorspacing * 5 = 5 units
        grid_spacing = majorspacing * 5
        
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
        
        x = first_x
        while x <= x_end:
            grid_line = self.scene.addLine(
                x, scene_rect.top(), x, scene_rect.bottom(), grid_pen
            )
            grid_line.setZValue(-1001)
            x += grid_spacing
        
        # Horizontal grid lines
        y_start = scene_rect.top()
        y_end = scene_rect.bottom()
        first_y = math.floor(y_start / grid_spacing) * grid_spacing
        
        y = first_y
        while y <= y_end:
            grid_line = self.scene.addLine(
                scene_rect.left(), y, scene_rect.right(), y, grid_pen
            )
            grid_line.setZValue(-1001)
            y += grid_spacing
    
    def _add_test_objects(self):
        """Add test objects to verify grid alignment"""
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
        
        # Add test shapes at grid positions (multiples of 5)
        test_pen = QPen(QColor(255, 0, 0))
        test_pen.setWidth(2)
        
        # Rectangle from (5,5) to (15,10)
        self.scene.addRect(5, 5, 10, 5, test_pen)
        
        # Circle at (10, -10) with radius 2.5
        circle_pen = QPen(QColor(0, 0, 255))
        circle_pen.setWidth(2)
        self.scene.addEllipse(7.5, -12.5, 5, 5, circle_pen)
        
        # Line from (-15, -5) to (-5, 5)
        line_pen = QPen(QColor(0, 128, 0))
        line_pen.setWidth(2)
        self.scene.addLine(-15, -5, -5, 5, line_pen)
        
        # Add some points at grid intersections
        point_pen = QPen(QColor(255, 128, 0))
        point_brush = QBrush(QColor(255, 128, 0))
        
        for x in [-10, 0, 10]:
            for y in [-10, 0, 10]:
                self.scene.addEllipse(x-1, y-1, 2, 2, point_pen, point_brush)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinalGridTest()
    window.show()
    sys.exit(app.exec())
