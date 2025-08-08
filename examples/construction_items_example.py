#!/usr/bin/env python3
"""Example demonstrating ConstructionLineItem and ConstructionCircleItem."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget
from PySide6.QtCore import QRectF, QPointF, QLineF
from PySide6.QtGui import QPen, QColor, QPainter
from BelfryCAD.gui.views.graphics_items.construction_line_item import ConstructionLineItem, ArrowTip, DashPattern as LineDashPattern
from BelfryCAD.gui.views.graphics_items.construction_circle_item import ConstructionCircleItem, DashPattern as CircleDashPattern

def construction_items_example():
    """Demonstrate construction line and circle items."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Set up view
    view.setSceneRect(-200, -200, 400, 400)
    view.fitInView(QRectF(-100, -100, 200, 200))
    
    print("Creating construction items...")
    
    # Create construction lines
    line1 = ConstructionLineItem(
        QLineF(QPointF(-80, -80), QPointF(80, -80)),
        dash_pattern=LineDashPattern.SOLID,
        arrow_tips=ArrowTip.BOTH
    )
    
    line2 = ConstructionLineItem(
        QLineF(QPointF(-80, 0), QPointF(80, 0)),
        dash_pattern=LineDashPattern.DASHED,
        arrow_tips=ArrowTip.END
    )
    
    line3 = ConstructionLineItem(
        QLineF(QPointF(-80, 80), QPointF(80, 80)),
        dash_pattern=LineDashPattern.CENTERLINE,
        arrow_tips=ArrowTip.START
    )
    
    # Create construction circles
    circle1 = ConstructionCircleItem(
        QRectF(-60, -60, 120, 120),
        dash_pattern=CircleDashPattern.SOLID
    )
    
    circle2 = ConstructionCircleItem(
        QRectF(60, -60, 120, 120),
        dash_pattern=CircleDashPattern.DASHED
    )
    
    circle3 = ConstructionCircleItem(
        QRectF(-60, 60, 120, 120),
        dash_pattern=CircleDashPattern.CENTERLINE
    )
    
    # Add all items to scene
    scene.addItem(line1)
    scene.addItem(line2)
    scene.addItem(line3)
    scene.addItem(circle1)
    scene.addItem(circle2)
    scene.addItem(circle3)
    
    print(f"Added {len(scene.items())} construction items to scene")
    
    # Show window
    window = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(view)
    window.setLayout(layout)
    window.resize(800, 600)
    window.show()
    
    print("Window shown. You should see:")
    print("  - Construction lines with different patterns and arrows")
    print("  - Construction circles with different patterns")
    print("  - All items in gray (#7f7f7f) color")
    print("  - All items are non-interactive")
    print("Close window to exit.")
    
    return app.exec()

if __name__ == "__main__":
    construction_items_example() 