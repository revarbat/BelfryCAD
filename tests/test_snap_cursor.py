#!/usr/bin/env python3
"""
Test script for SnapCursorItem X-shaped cross display.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtGui import QPainter
from BelfryCAD.gui.grid_graphics_items import SnapCursorItem
from BelfryCAD.gui.grid_info import GridInfo, GridUnits

def test_snap_cursor():
    """Test the SnapCursorItem X-shaped cross display."""
    print("Testing SnapCursorItem X-shaped cross display...")
    
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
    
    # Set up the view
    view.setSceneRect(-10, -10, 20, 20)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setViewportUpdateMode(view.ViewportUpdateMode.FullViewportUpdate)
    
    # Show the view
    view.resize(800, 600)
    view.show()
    
    print("SnapCursorItem test window opened!")
    print("- You should see a red X-shaped cross at the center of the view")
    print("- The cross should have a linewidth of 2 and be cosmetic (scale-independent)")
    print("- Close the window to end the test")
    
    return app.exec()

if __name__ == "__main__":
    test_snap_cursor() 