#!/usr/bin/env python3
"""
Manual test for pinch-to-zoom functionality in CADGraphicsView.

This script creates a simple GUI to test pinch-to-zoom gestures on a touchscreen device.
Use two fingers to pinch (zoom out) or spread (zoom in) on the graphics view.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

from BelfryCAD.gui.cad_graphics_view import CADGraphicsView
from BelfryCAD.gui.cad_scene import CadScene
from BelfryCAD.gui.drawing_manager import DrawingManager


class PinchZoomTestWindow(QMainWindow):
    """Simple test window for pinch-to-zoom functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pinch-to-Zoom Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create instructions label
        instructions = QLabel(
            "Pinch-to-Zoom Test Instructions:\n"
            "• Use two fingers to pinch in (zoom out)\n" 
            "• Use two fingers to spread out (zoom in)\n"
            "• Two-finger pan should still work for scrolling\n"
            "• Ctrl+mouse wheel zoom should also work\n"
            "Current zoom will be displayed in window title"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        # Create CAD graphics view
        self.graphics_view = CADGraphicsView()
        layout.addWidget(self.graphics_view)
        
        # Create CAD scene and drawing manager
        self.cad_scene = CadScene()
        self.drawing_manager = DrawingManager()
        self.drawing_manager.cad_scene = self.cad_scene
        
        # Set up the graphics view
        self.graphics_view.set_drawing_manager(self.drawing_manager)
        self.graphics_view.setScene(self.cad_scene)
        
        # Add some simple drawing content for visual reference
        self.add_test_content()
        
        # Connect to scale factor changes to update title
        self.cad_scene.scale_changed.connect(self.update_zoom_display)
        
        # Initial zoom display
        self.update_zoom_display()
    
    def add_test_content(self):
        """Add some basic content to the scene for visual reference"""
        from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem
        from PySide6.QtGui import QPen
        from PySide6.QtCore import QRectF
        
        # Add some rectangles and circles as reference
        pen = QPen(Qt.GlobalColor.blue, 2)
        
        # Rectangle
        rect = QGraphicsRectItem(QRectF(-100, -100, 200, 100))
        rect.setPen(pen)
        self.cad_scene.addItem(rect)
        
        # Circle
        circle = QGraphicsEllipseItem(QRectF(-50, 50, 100, 100))
        circle.setPen(pen)
        self.cad_scene.addItem(circle)
        
        # Another rectangle
        rect2 = QGraphicsRectItem(QRectF(50, -50, 150, 75))
        rect2.setPen(QPen(Qt.GlobalColor.red, 2))
        self.cad_scene.addItem(rect2)
    
    def update_zoom_display(self):
        """Update the window title with current zoom level"""
        zoom_percent = int(self.cad_scene.scale_factor * 100)
        self.setWindowTitle(f"Pinch-to-Zoom Test - Zoom: {zoom_percent}%")


def run_pinch_zoom_test():
    """Run the manual pinch-to-zoom test"""
    app = QApplication(sys.argv)
    
    # Create and show the test window
    window = PinchZoomTestWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == '__main__':
    print("Starting Pinch-to-Zoom Manual Test...")
    print("Use a touchscreen device to test two-finger pinch and spread gestures.")
    run_pinch_zoom_test()
