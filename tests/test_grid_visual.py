#!/usr/bin/env python3
"""
Visual test of grid lines with some test objects to verify proper layering.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QBrush

from BelfryCAD.gui.cad_graphics_view import CADGraphicsView
from BelfryCAD.gui.rulers import RulerManager
from PySide6.QtWidgets import QGraphicsScene


class GridVisualTestWindow(QMainWindow):
    """Visual test window to verify grid with test objects."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid Visual Test - PyTkCAD")
        self.resize(1000, 800)
        self._setup_ui()
        self._add_test_objects()

    def _setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create graphics scene and view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-3000, -3000, 6000, 6000)

        self.canvas = CADGraphicsView()
        self.canvas.setScene(self.scene)

        # Create rulers
        self.ruler_manager = RulerManager(self.canvas, central_widget)
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        vertical_ruler = self.ruler_manager.get_vertical_ruler()

        # Corner widget
        corner_widget = QWidget()
        corner_widget.setFixedSize(32, 32)
        corner_widget.setStyleSheet("background-color: white; border: 1px solid black;")

        # Layout grid
        layout.addWidget(corner_widget, 0, 0)
        layout.addWidget(horizontal_ruler, 0, 1)
        layout.addWidget(vertical_ruler, 1, 0)
        layout.addWidget(self.canvas, 1, 1)

        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)

        # Add axis lines and grid first (behind everything)
        self._add_axis_lines()
        self._add_grid_lines()

        # Connect events
        self._connect_events()

    def _add_axis_lines(self):
        """Add axis lines at X=0 and Y=0"""
        axis_pen = QPen(QColor(128, 128, 128))
        axis_pen.setWidth(2)

        scene_rect = self.scene.sceneRect()
        h_axis = self.scene.addLine(scene_rect.left(), 0, scene_rect.right(), 0, axis_pen)
        v_axis = self.scene.addLine(0, scene_rect.top(), 0, scene_rect.bottom(), axis_pen)

        h_axis.setZValue(-1000)
        v_axis.setZValue(-1000)

    def _add_grid_lines(self):
        """Add dotted grid lines that align with ruler major tickmarks"""
        # Get grid information from ruler
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = horizontal_ruler.get_grid_info()

        # Create dotted pen for grid
        grid_pen = QPen(QColor(200, 200, 200))
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.DotLine)

        scene_rect = self.scene.sceneRect()

        # Vertical grid lines (align with horizontal ruler major ticks)
        import math
        x_start = scene_rect.left()
        x_end = scene_rect.right()
        first_x = math.floor(x_start / labelspacing) * labelspacing

        x = first_x
        while x <= x_end:
            if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
                grid_line = self.scene.addLine(
                    x, scene_rect.top(), x, scene_rect.bottom(), grid_pen
                )
                grid_line.setZValue(-1001)
            x += labelspacing

        # Horizontal grid lines (align with vertical ruler major ticks)
        y_start = scene_rect.top()
        y_end = scene_rect.bottom()
        first_y = math.floor(y_start / labelspacing) * labelspacing

        y = first_y
        while y <= y_end:
            if abs(math.floor(y / labelspacing + 1e-6) - y / labelspacing) < 1e-3:
                grid_line = self.scene.addLine(
                    scene_rect.left(), y, scene_rect.right(), y, grid_pen
                )
                grid_line.setZValue(-1001)
            y += labelspacing

        print(f"Grid added with spacing: {labelspacing} units")
        print(f"Grid range X: {x_start} to {x_end}")
        print(f"Grid range Y: {y_start} to {y_end}")

    def _add_test_objects(self):
        """Add some test objects to verify grid alignment and layering"""
        # Create various drawing objects to test with grid

        # Test lines at grid intersections
        line_pen = QPen(QColor(255, 0, 0))  # Red
        line_pen.setWidth(2)

        # Draw lines from origin to grid points
        self.scene.addLine(0, 0, 3, 0, line_pen)  # Horizontal line to (3,0)
        self.scene.addLine(0, 0, 0, 2, line_pen)  # Vertical line to (0,2)
        self.scene.addLine(0, 0, 2, 2, line_pen)  # Diagonal line to (2,2)

        # Test rectangles aligned with grid
        rect_pen = QPen(QColor(0, 0, 255))  # Blue
        rect_pen.setWidth(1)
        rect_brush = QBrush(QColor(0, 0, 255, 50))  # Semi-transparent blue

        # Rectangle from (1,1) to (3,2) - should align with grid
        self.scene.addRect(1, 1, 2, 1, rect_pen, rect_brush)

        # Test circles at grid intersections
        circle_pen = QPen(QColor(0, 255, 0))  # Green
        circle_pen.setWidth(2)

        # Circle centered at (-2, -1) with radius 0.5
        self.scene.addEllipse(-2.5, -1.5, 1, 1, circle_pen)

        # Circle centered at (4, 3) with radius 0.5
        self.scene.addEllipse(3.5, 2.5, 1, 1, circle_pen)

        # Add some points at exact grid intersections
        point_pen = QPen(QColor(255, 0, 255))  # Magenta
        point_brush = QBrush(QColor(255, 0, 255))

        # Points at grid intersections
        grid_points = [(-1, -1), (0, 1), (1, 0), (2, -2), (-3, 2)]
        for x, y in grid_points:
            self.scene.addEllipse(x-0.1, y-0.1, 0.2, 0.2, point_pen, point_brush)

        print("Test objects added:")
        print("- Red lines from origin")
        print("- Blue rectangle at (1,1) to (3,2)")
        print("- Green circles at (-2,-1) and (4,3)")
        print("- Magenta points at grid intersections")

    def _connect_events(self):
        """Connect scroll events to ruler updates"""
        def update_rulers():
            self.ruler_manager.update_rulers()

        self.canvas.horizontalScrollBar().valueChanged.connect(update_rulers)
        self.canvas.verticalScrollBar().valueChanged.connect(update_rulers)

        # Mouse tracking for ruler position indicators
        original_mouse_move = self.canvas.mouseMoveEvent

        def enhanced_mouse_move(event):
            original_mouse_move(event)
            scene_pos = self.canvas.mapToScene(event.pos())
            self.ruler_manager.update_mouse_position(scene_pos.x(), scene_pos.y())

        self.canvas.mouseMoveEvent = enhanced_mouse_move


def main():
    app = QApplication(sys.argv)

    window = GridVisualTestWindow()
    window.show()

    print("\nGrid Visual Test Instructions:")
    print("- The grid should appear as light gray dotted lines")
    print("- Grid lines should align exactly with ruler major tickmarks")
    print("- Test objects should be drawn on top of the grid")
    print("- Scroll around to verify grid updates correctly")
    print("- Grid lines should be at 1-unit intervals")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
