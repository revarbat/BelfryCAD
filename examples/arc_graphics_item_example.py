#!/usr/bin/env python3
"""
Example script demonstrating ArcGraphicsItem usage.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor

# Import the arc graphics item
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'gui', 'views', 'graphics_items'))
from cad_arc_graphics_item import CadArcGraphicsItem, CadArcArrowheadEndcaps


def main():
    """Demonstrate ArcGraphicsItem usage."""
    print("=== ArcGraphicsItem Example ===\n")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("ArcGraphicsItem Example")
    window.setGeometry(100, 100, 600, 400)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    # Create layout
    layout = QVBoxLayout(central_widget)
    
    # Create graphics view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    layout.addWidget(view)
    
    # Set up the view
    scene.setSceneRect(-150, -150, 300, 300)
    view.setRenderHint(view.renderHints().Antialiasing)
    
    # Create reference items
    from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem
    from PySide6.QtGui import QPen
    
    # Center point
    center_dot = QGraphicsEllipseItem(-2, -2, 4, 4)
    center_dot.setBrush(QColor(255, 0, 0))
    scene.addItem(center_dot)
    
    # Reference lines
    x_axis = QGraphicsLineItem(-120, 0, 120, 0)
    x_axis.setPen(QPen(QColor(200, 200, 200), 1))
    scene.addItem(x_axis)
    
    y_axis = QGraphicsLineItem(0, -120, 0, 120)
    y_axis.setPen(QPen(QColor(200, 200, 200), 1))
    scene.addItem(y_axis)
    
    # Example 1: Quarter circle (0° to 90°)
    print("Creating quarter circle arc (0° to 90°)...")
    arc1 = CadArcGraphicsItem(
        center_point=QPointF(0, 0),
        radius=80,
        start_angle=0,
        span_angle=90,
        arrowheads=CadArcArrowheadEndcaps.BOTH
    )
    arc1.setPen(QPen(QColor(0, 0, 255), 3.0))
    scene.addItem(arc1)
    
    # Example 2: Semicircle (180° to 360°)
    print("Creating semicircle arc (180° to 360°)...")
    arc2 = CadArcGraphicsItem(
        center_point=QPointF(0, 0),
        radius=60,
        start_angle=180,
        span_angle=180,
        arrowheads=CadArcArrowheadEndcaps.NONE
    )
    arc2.setPen(QPen(QColor(255, 0, 0), 2.0))
    scene.addItem(arc2)
    
    # Example 3: Small arc with negative span
    print("Creating small arc with negative span (45° to 15°)...")
    arc3 = CadArcGraphicsItem(
        center_point=QPointF(0, 0),
        radius=40,
        start_angle=45,
        span_angle=-30,
        arrowheads=CadArcArrowheadEndcaps.BOTH
    )
    arc3.setPen(QPen(QColor(0, 255, 0), 2.0))
    scene.addItem(arc3)
    
    # Example 4: Dashed arc
    print("Creating dashed arc (270° to 360°)...")
    arc4 = CadArcGraphicsItem(
        center_point=QPointF(0, 0),
        radius=100,
        start_angle=270,
        span_angle=90,
        arrowheads=CadArcArrowheadEndcaps.BOTH
    )
    arc4.setPen(QPen(QColor(255, 255, 0), 2.0, Qt.PenStyle.DashLine))
    scene.addItem(arc4)
    
    # Show the window
    window.show()
    
    print("\nArcGraphicsItem examples created successfully!")
    print("Blue arc: Quarter circle (0° to 90°) with arrowheads")
    print("Red arc: Semicircle (180° to 360°) without arrowheads")
    print("Green arc: Small arc (45° to 15°) with arrowheads")
    print("Yellow arc: Dashed arc (270° to 360°) with arrowheads")
    print("\nNote: In a CadView, Y+ is up, so 0° points right, 90° points up.")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 