#!/usr/bin/env python3
"""
Test grid alignment with ruler major tickmarks
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
import math

class GridAlignmentTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Alignment Test - Should Match Ruler Ticks")
        self.resize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create scene and canvas
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-20, -20, 40, 40)
        
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
        
        # Add grid using EXACT same logic as main window
        self._add_aligned_grid()
        self._add_test_objects()
    
    def _add_aligned_grid(self):
        """Add grid using exact same logic as main window"""
        # Get grid info exactly like main window
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        grid_info = horizontal_ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info
        
        print(f"Grid parameters:")
        print(f"  minorspacing: {minorspacing}")
        print(f"  majorspacing: {majorspacing}")
        print(f"  labelspacing: {labelspacing}")
        print(f"  superspacing: {superspacing}")
        
        # Create grid pen exactly like main window
        grid_pen = QPen(QColor(200, 200, 200))
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DotLine)
        
        scene_rect = self.scene.sceneRect()
        grid_spacing = labelspacing
        
        print(f"Using grid_spacing = {grid_spacing} (labelspacing)")
        
        # Vertical grid lines - exact same logic
        x_start = scene_rect.left()
        x_end = scene_rect.right()
        first_x = math.floor(x_start / grid_spacing + 1e-6) * grid_spacing
        
        print(f"Vertical lines: from {first_x} to {x_end}")
        
        x = first_x
        v_count = 0
        while x <= x_end and v_count < 50:  # Safety limit
            # Use exact same test as ruler
            if abs(math.floor(x / grid_spacing + 1e-6) - x / grid_spacing) < 1e-3:
                grid_line = self.scene.addLine(
                    x, scene_rect.top(), x, scene_rect.bottom(), grid_pen
                )
                grid_line.setZValue(-1001)
                print(f"  Vertical grid line at x={x}")
                v_count += 1
            x += minorspacing
        
        # Horizontal grid lines - exact same logic
        y_start = scene_rect.top()
        y_end = scene_rect.bottom()
        first_y = math.floor(y_start / grid_spacing + 1e-6) * grid_spacing
        
        print(f"Horizontal lines: from {first_y} to {y_end}")
        
        y = first_y
        h_count = 0
        while y <= y_end and h_count < 50:  # Safety limit
            # Use exact same test as ruler
            if abs(math.floor(y / grid_spacing + 1e-6) - y / grid_spacing) < 1e-3:
                grid_line = self.scene.addLine(
                    scene_rect.left(), y, scene_rect.right(), y, grid_pen
                )
                grid_line.setZValue(-1001)
                print(f"  Horizontal grid line at y={y}")
                h_count += 1
            y += minorspacing
        
        print(f"Total grid lines: {v_count} vertical, {h_count} horizontal")
    
    def _add_test_objects(self):
        """Add test objects at expected grid positions"""
        # Add axis lines
        axis_pen = QPen(QColor(128, 128, 128))
        axis_pen.setWidth(2)
        
        scene_rect = self.scene.sceneRect()
        
        # Axes
        h_axis = self.scene.addLine(
            scene_rect.left(), 0, scene_rect.right(), 0, axis_pen
        )
        h_axis.setZValue(-1000)
        
        v_axis = self.scene.addLine(
            0, scene_rect.top(), 0, scene_rect.bottom(), axis_pen
        )
        v_axis.setZValue(-1000)
        
        # Test shapes at grid positions
        test_pen = QPen(QColor(255, 0, 0))
        test_pen.setWidth(2)
        
        # Small rectangles at expected grid intersections
        for x in [-10, -5, 0, 5, 10]:
            for y in [-10, -5, 0, 5, 10]:
                self.scene.addRect(x-0.2, y-0.2, 0.4, 0.4, test_pen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GridAlignmentTest()
    window.show()
    sys.exit(app.exec())
