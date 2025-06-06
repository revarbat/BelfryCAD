#!/usr/bin/env python3
"""
Test the fixed grid implementation to verify alignment with rulers
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from PySide6.QtGui import QPen, QColor, QBrush
from PySide6.QtCore import Qt
from BelfryCAD.gui.main_window import CADGraphicsView
from BelfryCAD.gui.rulers import RulerManager
from PySide6.QtWidgets import QGraphicsScene


class GridFixTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Fix Test - Aligned with Ruler Major Ticks")
        self.resize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create scene and canvas
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-15, -15, 30, 30)
        
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
        self._add_fixed_grid()
        self._add_test_objects()
        
        print("Grid Fix Test Created:")
        print("- Grid should now align perfectly with ruler major ticks")
        print("- Test objects at grid intersections for verification")
        print("- Compare grid lines with ruler tickmarks")
    
    def _add_fixed_grid(self):
        """Add grid using the fixed logic that matches rulers exactly"""
        # Get grid info from ruler
        h_ruler = self.ruler_manager.get_horizontal_ruler()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = h_ruler.get_grid_info()
        
        print(f"Grid parameters: minorspacing={minorspacing}, labelspacing={labelspacing}")
        
        # Create grid pen
        grid_pen = QPen(QColor(200, 200, 200))
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DotLine)
        
        scene_rect = self.scene.sceneRect()
        
        # Use EXACT same logic as ruler for vertical grid lines
        import math
        x_start = scene_rect.left()
        x_end = scene_rect.right()
        
        # Start from first minor tick position (ruler logic)
        x = math.floor(x_start / minorspacing + 1e-6) * minorspacing
        
        grid_count = 0
        while x <= x_end and grid_count < 50:  # Safety limit
            # Test if this position would be a major tick with label (ruler logic)
            if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
                grid_line = self.scene.addLine(
                    x, scene_rect.top(), x, scene_rect.bottom(), grid_pen
                )
                grid_line.setZValue(-1001)
                print(f"Vertical grid line at x={x}")
                grid_count += 1
            x += minorspacing
        
        # Use EXACT same logic as ruler for horizontal grid lines
        y_start = scene_rect.top()
        y_end = scene_rect.bottom()
        
        # Start from first minor tick position (ruler logic)
        y = math.floor(y_start / minorspacing + 1e-6) * minorspacing
        
        grid_count = 0
        while y <= y_end and grid_count < 50:  # Safety limit
            # Test if this position would be a major tick with label (ruler logic)
            if abs(math.floor(y / labelspacing + 1e-6) - y / labelspacing) < 1e-3:
                grid_line = self.scene.addLine(
                    scene_rect.left(), y, scene_rect.right(), y, grid_pen
                )
                grid_line.setZValue(-1001)
                print(f"Horizontal grid line at y={y}")
                grid_count += 1
            y += minorspacing
    
    def _add_test_objects(self):
        """Add test objects at grid intersections to verify alignment"""
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
        
        # Add test markers at expected grid intersections
        marker_pen = QPen(QColor(255, 0, 0))
        marker_pen.setWidth(3)
        marker_brush = QBrush(QColor(255, 0, 0))
        
        # Test at integer positions (should align with grid)
        for x in [-10, -5, 0, 5, 10]:
            for y in [-10, -5, 0, 5, 10]:
                # Small circle at grid intersection
                self.scene.addEllipse(
                    x-0.3, y-0.3, 0.6, 0.6, 
                    marker_pen, marker_brush
                )
        
        # Add a test rectangle that should align with grid
        rect_pen = QPen(QColor(0, 0, 255))
        rect_pen.setWidth(2)
        self.scene.addRect(-3, -2, 6, 4, rect_pen)
        
        print("Test objects added:")
        print("- Red dots at integer grid intersections")
        print("- Blue rectangle from (-3,-2) to (3,2)")
        print("- Should all align perfectly with grid lines")


def main():
    app = QApplication(sys.argv)
    
    window = GridFixTest()
    window.show()
    
    print("\nInstructions:")
    print("1. Check that grid lines align exactly with ruler major tickmarks")
    print("2. Red dots should be at grid intersections") 
    print("3. Blue rectangle should align with grid")
    print("4. Try scrolling - grid should update and stay aligned")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
