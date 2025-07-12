#!/usr/bin/env python3
"""
Test script for SnapCursorItem X-shaped shape method.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtGui import QPainter
from ..src.BelfryCAD.gui.views.graphics_items.grid_graphics_items import SnapCursorItem
from ..src.BelfryCAD.gui.grid_info import GridInfo, GridUnits

def test_snap_cursor_shape():
    """Test the SnapCursorItem X-shaped shape method."""
    print("Testing SnapCursorItem X-shaped shape method...")
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    # Create grid info
    grid_info = GridInfo(GridUnits.INCHES_DECIMAL)
    
    # Create snap cursor item
    snap_cursor = SnapCursorItem()
    snap_cursor.setPos(QPointF(0, 0))  # Position at origin
    scene.addItem(snap_cursor)
    
    # Test the shape method
    shape = snap_cursor.shape()
    print(f"Shape path element count: {shape.elementCount()}")
    print(f"Shape bounding rect: {shape.boundingRect()}")
    
    # Test hit testing at different points
    test_points = [
        QPointF(0, 0),      # Center
        QPointF(0.1, 0.1),  # Near center
        QPointF(0.5, 0.5),  # On diagonal
        QPointF(-0.5, -0.5), # On diagonal
        QPointF(1, 1),      # Outside
        QPointF(-1, -1),    # Outside
    ]
    
    for point in test_points:
        contains = shape.contains(point)
        print(f"Point {point.x():.1f}, {point.y():.1f}: {'contains' if contains else 'does not contain'}")
    
    # Set up the view
    view.setSceneRect(-2, -2, 4, 4)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setViewportUpdateMode(view.ViewportUpdateMode.FullViewportUpdate)
    
    # Show the view
    view.resize(600, 400)
    view.show()
    
    print("\nSnapCursorItem shape test window opened!")
    print("- The X-shaped cross should be visible")
    print("- Hit testing should work around the X shape")
    print("- Close the window to end the test")
    
    return app.exec()

if __name__ == "__main__":
    test_snap_cursor_shape() 