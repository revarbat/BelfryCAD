"""
Test script for QGraphicsView and QGraphicsScene functionality.
"""

import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QLabel,
)
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPen, QColor, QPainter, QBrush,
    QKeySequence, QShortcut, QCursor,
)

sys.path.insert(0, '/Users/gminette/dev/git-repos/BelfryCAD')

from BelfryCAD.gui.grid_info import GridInfo, GridUnits
from BelfryCAD.gui.grid_graphics_items import GridBackground, RulersForeground
from BelfryCAD.gui.zoom_edit_widget import ZoomEditWidget
from BelfryCAD.gui.caditems import LineCadItem, PolylineCadItem, CircleCenterRadiusCadItem, CubicBezierCadItem, RectangleCadItem, ArcCadItem
from BelfryCAD.gui.cad_view import CadView
from BelfryCAD.gui.cad_scene import CadScene


class TestGraphicsWindow(QMainWindow):
    """Test window with graphics view and zoom controls."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graphics View Test")
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create graphics scene and view
        self.scene = CadScene()
        self.view = CadView(self.scene)
        self.view.mouseMoveEvent = self._mouse_move_event  # Override mouse move event
        layout.addWidget(self.view)

        # Create control buttons
        controls_layout = QHBoxLayout()
        # Add keyboard shortcuts

        # Position label
        self.position_label_x = QLabel("X: 0.000")
        self.position_label_x.setMinimumWidth(100)
        self.position_label_x.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.position_label_y = QLabel("Y: 0.000")
        self.position_label_y.setMinimumWidth(100)
        self.position_label_y.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        controls_layout.addWidget(self.position_label_x)
        controls_layout.addWidget(self.position_label_y)

        # Zoom edit widget
        self.zoom_edit_widget = ZoomEditWidget(self.view)
        controls_layout.addLayout(self.zoom_edit_widget)
        self.zoom_edit_widget.set_zoom_value(GridInfo.get_zoom(self.view))

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Add grid background
        self.grid_info = GridInfo(GridUnits.INCHES_DECIMAL)
        self.grid = GridBackground(self.grid_info)
        self.scene.addItem(self.grid)

        # Add rulers
        self.rulers = RulersForeground(self.grid_info)
        self.scene.addItem(self.rulers)

        # Draw test shapes
        self._draw_shapes()

    def _draw_shapes(self):
        """Draw test shapes on the scene."""
        black = QColor(0, 0, 0)

        # Add draggable circles
        circle1 = CircleCenterRadiusCadItem(
            QPointF(1, 0.5), QPointF(2, 0.5),
            black, 0.08)
        circle1.setZValue(2)  # Above other shapes
        self.scene.addItem(circle1)
        
        # Add polylines
        # Triangle polyline
        triangle_points = [
            QPointF(-3, 0),
            QPointF(-1, 0),
            QPointF(-2, 2),
            QPointF(-3, 0)
        ]
        triangle = PolylineCadItem(
            triangle_points, black, 0.1)
        triangle.setZValue(1)
        self.scene.addItem(triangle)
        
        # Zigzag polyline
        zigzag_points = [
            QPointF(-4, -2),
            QPointF(-3, -1),
            QPointF(-2, -2), 
            QPointF(-1, -1),
            QPointF(0, -2),
            QPointF(1, -1)
        ]
        zigzag = PolylineCadItem(
            zigzag_points, black, 0.08)
        zigzag.setZValue(2)
        self.scene.addItem(zigzag)
                
        # Add line segments
        # Horizontal line
        line1 = LineCadItem(
            QPointF(-2, 4), QPointF(2, 4),
            black, 0.12)
        line1.setZValue(1)
        self.scene.addItem(line1)
        
        # Diagonal line
        line2 = LineCadItem(
            QPointF(-4, 1), QPointF(-2, 3),
            black, 0.08)
        line2.setZValue(2)
        self.scene.addItem(line2)
        
        # Vertical line
        line3 = LineCadItem(
            QPointF(4, -2), QPointF(4, 2),
            black, 0.1)
        line3.setZValue(2)
        self.scene.addItem(line3)
        
        # Add Bezier curves
        # Tight curve
        bezier3 = CubicBezierCadItem(
            QPointF(-1, 1.5), QPointF(0, 3.5), 
            QPointF(1, 3.5), QPointF(2, 2),
            black, 0.1)
        bezier3.setZValue(2)
        self.scene.addItem(bezier3)
        
        # Add rectangles
        # Test rectangle
        rectangle1 = RectangleCadItem(
            QPointF(3, 3), QPointF(5, 3),
            QPointF(5, 1), QPointF(3, 1),
            black, 0.08)
        rectangle1.setZValue(2)
        self.scene.addItem(rectangle1)
        
        # Add arcs
        # Test arc (quarter circle)
        arc1 = ArcCadItem(
            QPointF(-1, -3), QPointF(0, -3), QPointF(-1, -2),
            black, 0.1)
        arc1.setZValue(2)
        self.scene.addItem(arc1)
        



def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    window = TestGraphicsWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 