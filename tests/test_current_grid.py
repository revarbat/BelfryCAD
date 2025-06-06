#!/usr/bin/env python3
"""
Test current grid implementation in main window to check alignment
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
import math

class CurrentGridTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Current Grid Test - Check Alignment")
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

        # Add axis lines and test current grid implementation
        self._add_axis_lines()
        self._add_current_grid()
        self._add_ruler_tick_markers()

        print("Current Grid Test Created:")
        print("- Uses EXACT same logic as MainWindow._add_grid_lines()")
        print("- Red markers show expected ruler major tick positions")
        print("- Grid lines should align with red markers")

    def _add_axis_lines(self):
        """Add axis lines"""
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

    def _add_current_grid(self):
        """Add grid using EXACT same logic as MainWindow._add_grid_lines()"""
        # Get grid information from the ruler system
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        grid_info = horizontal_ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info

        print(f"Grid parameters:")
        print(f"  minorspacing: {minorspacing}")
        print(f"  majorspacing: {majorspacing}")
        print(f"  labelspacing: {labelspacing}")

        # Create a light gray dotted pen for grid lines
        grid_pen = QPen(QColor(200, 200, 200))  # Light gray
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DotLine)  # Dotted line style

        # Get the visible scene rectangle
        scene_rect = self.scene.sceneRect()

        # Draw vertical grid lines
        # Use EXACT same logic as horizontal ruler's _draw_horizontal_ruler
        x_start = scene_rect.left()
        x_end = scene_rect.right()

        # Start from first minor tick position (ruler logic)
        x = math.floor(x_start / minorspacing + 1e-6) * minorspacing

        grid_count = 0
        while x <= x_end and grid_count < 50:  # Safety limit
            # Test if this position would be a major tick with label
            if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
                grid_line = self.scene.addLine(
                    x, scene_rect.top(),
                    x, scene_rect.bottom(),
                    grid_pen
                )
                # Put grid lines behind axis lines
                grid_line.setZValue(-1001)
                print(f"Vertical grid line at x={x}")
                grid_count += 1
            x += minorspacing  # Iterate by minorspacing (ruler logic)

        # Draw horizontal grid lines
        # Use EXACT same logic as vertical ruler's _draw_vertical_ruler
        y_start = scene_rect.top()
        y_end = scene_rect.bottom()

        # Start from first minor tick position (ruler logic)
        y = math.floor(y_start / minorspacing + 1e-6) * minorspacing

        grid_count = 0
        while y <= y_end and grid_count < 50:  # Safety limit
            # Test if this position would be a major tick with label
            if abs(math.floor(y / labelspacing + 1e-6) - y / labelspacing) < 1e-3:
                grid_line = self.scene.addLine(
                    scene_rect.left(), y,
                    scene_rect.right(), y,
                    grid_pen
                )
                # Put grid lines behind axis lines
                grid_line.setZValue(-1001)
                print(f"Horizontal grid line at y={y}")
                grid_count += 1
            y += minorspacing  # Iterate by minorspacing (ruler logic)

    def _add_ruler_tick_markers(self):
        """Add red markers where ruler major ticks should be"""
        # Get grid info
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        grid_info = horizontal_ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info

        # Red markers for expected major tick positions
        marker_pen = QPen(QColor(255, 0, 0))
        marker_pen.setWidth(4)
        marker_brush = QBrush(QColor(255, 0, 0))

        scene_rect = self.scene.sceneRect()

        # Place red markers at integer positions (where labels should be)
        for pos in range(-15, 16):
            # Check if this matches the ruler's major tick logic
            if abs(math.floor(pos / labelspacing + 1e-6) - pos / labelspacing) < 1e-3:
                # Vertical marker (for horizontal position)
                self.scene.addEllipse(pos-0.2, -0.5, 0.4, 1.0, marker_pen, marker_brush)
                # Horizontal marker (for vertical position)
                self.scene.addEllipse(-0.5, pos-0.2, 1.0, 0.4, marker_pen, marker_brush)
                print(f"Ruler major tick marker at {pos}")

def main():
    app = QApplication(sys.argv)

    window = CurrentGridTest()
    window.show()

    print("\nInstructions:")
    print("1. Red markers show where ruler major ticks should be")
    print("2. Grid lines should align exactly with red markers")
    print("3. If grid lines don't align, there's still an issue")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
