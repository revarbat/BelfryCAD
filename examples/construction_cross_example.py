#!/usr/bin/env python3
"""Example demonstrating ConstructionCrossItem for marking circle centers."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget
from PySide6.QtCore import QRectF, QPointF, QLineF
from PySide6.QtGui import QPen, QColor, QPainter
from BelfryCAD.gui.views.graphics_items.construction_line_item import ConstructionLineItem, ArrowTip, DashPattern as LineDashPattern
from BelfryCAD.gui.views.graphics_items.construction_circle_item import ConstructionCircleItem, DashPattern as CircleDashPattern
from BelfryCAD.gui.views.graphics_items.construction_cross_item import ConstructionCrossItem, DashPattern as CrossDashPattern

def construction_cross_example():
    """Demonstrate construction crosshairs marking circle centers."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Set up view
    view.setSceneRect(-200, -200, 400, 400)
    view.fitInView(QRectF(-100, -100, 200, 200))
    
    print("Creating construction items with center marks...")
    
    # Create construction circles with center crosshairs
    circle1 = ConstructionCircleItem(
        center=QPointF(-60, -60),
        radius=40,
        dash_pattern=CircleDashPattern.SOLID
    )
    
    cross1 = ConstructionCrossItem(
        center=QPointF(-60, -60),
        size=20,
        dash_pattern=CrossDashPattern.CENTERLINE
    )
    
    circle2 = ConstructionCircleItem(
        center=QPointF(60, -60),
        radius=40,
        dash_pattern=CircleDashPattern.DASHED
    )
    
    cross2 = ConstructionCrossItem(
        center=QPointF(60, -60),
        size=20,
        dash_pattern=CrossDashPattern.CENTERLINE
    )
    
    circle3 = ConstructionCircleItem(
        center=QPointF(0, 60),
        radius=40,
        dash_pattern=CircleDashPattern.CENTERLINE
    )
    
    cross3 = ConstructionCrossItem(
        center=QPointF(0, 60),
        size=20,
        dash_pattern=CrossDashPattern.CENTERLINE
    )
    
    # Add all items to scene
    scene.addItem(circle1)
    scene.addItem(cross1)
    scene.addItem(circle2)
    scene.addItem(cross2)
    scene.addItem(circle3)
    scene.addItem(cross3)
    
    print(f"Added {len(scene.items())} construction items to scene")
    
    # Show window
    window = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(view)
    window.setLayout(layout)
    window.resize(800, 600)
    window.show()
    
    print("Window shown. You should see:")
    print("  - Three construction circles with different patterns")
    print("  - Centerline crosshairs marking each circle center")
    print("  - All items in gray (#7f7f7f) color")
    print("  - All items are non-interactive")
    print("Close window to exit.")
    
    return app.exec()

if __name__ == "__main__":
    construction_cross_example() 