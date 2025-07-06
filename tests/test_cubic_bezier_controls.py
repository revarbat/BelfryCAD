#!/usr/bin/env python3
"""
Simple test for control points on multi-segment CubicBezierCadItem.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from ..src.BelfryCAD.gui.widgets.cad_scene import CadScene
from ..src.BelfryCAD.gui.widgets.cad_view import CadView
from ..src.BelfryCAD.gui.graphics_items.caditems.cubic_bezier_cad_item import CubicBezierCadItem


def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Multi-Segment Cubic Bezier Control Points Test")
    window.resize(800, 600)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    # Create CAD scene and view
    scene = CadScene()
    view = CadView(scene)
    layout.addWidget(view)
    
    # Create a 2-segment curve
    points = [
        QPointF(0, 0),      # 1st path point
        QPointF(1, 1),      # control1 for 1st segment
        QPointF(2, -1),     # control2 for 1st segment
        QPointF(3, 0),      # 2nd path point
        QPointF(4, 1),      # control1 for 2nd segment
        QPointF(5, -1),     # control2 for 2nd segment
        QPointF(6, 0),      # 3rd path point
    ]
    
    bezier = CubicBezierCadItem(points=points, color=QColor(0, 0, 255))
    scene.addItem(bezier)
    
    # Set view to show the curve
    view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    window.show()
    
    # Select the curve to show control points
    scene.clearSelection()
    bezier.setSelected(True)
    
    print("Multi-segment cubic Bezier curve created with control points.")
    print("Click and drag the control points to modify the curve.")
    print("Square control points are on the path, circular ones are control points.")
    
    return app.exec()


if __name__ == "__main__":
    main() 