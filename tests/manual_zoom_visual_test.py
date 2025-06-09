#!/usr/bin/env python3
"""
Manual test to verify that zoom operations result in visual changes.
This test creates a simple graphics scene and tests both Ctrl+wheel 
and pinch-to-zoom to ensure the visual scaling works.
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BelfryCAD.gui.cad_graphics_view import CADGraphicsView
from BelfryCAD.gui.cad_scene import CadScene

class ZoomTestWindow(QMainWindow):
    """Simple test window to verify zoom functionality"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zoom Visual Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create instruction label
        instructions = QLabel("""
        Zoom Visual Test Instructions:
        
        1. Ctrl + Mouse Wheel: Should zoom in/out (20% per step)
        2. Two-finger pinch/spread: Should zoom in/out (trackpad)
        3. Normal scroll: Should pan the view
        
        Watch the grid and any drawn elements to see if they scale visually.
        """)
        layout.addWidget(instructions)
        
        # Create and setup the CAD graphics view
        self.graphics_view = CADGraphicsView()
        
        # Create a mock scene with grid for visual reference
        self.cad_scene = CadScene()
        self.cad_scene.show_grid = True
        self.cad_scene.grid_spacing = 50.0
        
        # Create a mock drawing manager
        class MockDrawingManager:
            def __init__(self, cad_scene):
                self.cad_scene = cad_scene
        
        mock_drawing_manager = MockDrawingManager(self.cad_scene)
        self.graphics_view.set_drawing_manager(mock_drawing_manager)
        
        layout.addWidget(self.graphics_view)
        
        # Create status label to show current scale
        self.status_label = QLabel("Scale: 1.0")
        layout.addWidget(self.status_label)
        
        # Connect to scale changes to update status
        self.cad_scene.scale_changed.connect(self.on_scale_changed)
        
        print("✓ Zoom visual test window created")
        print("✓ Graphics view connected to CadScene")
        print("✓ Scale change signal connected")
        print("\nTest Ctrl+wheel and pinch gestures to verify visual zoom!")
    
    def on_scale_changed(self, scale_factor):
        """Update status when scale changes"""
        self.status_label.setText(f"Scale: {scale_factor:.3f}")
        print(f"Scale changed to: {scale_factor:.3f}")

def main():
    """Run the visual zoom test"""
    app = QApplication(sys.argv)
    
    window = ZoomTestWindow()
    window.show()
    
    print("\n🔍 Visual Zoom Test Running...")
    print("Try Ctrl+wheel and pinch gestures to test zoom functionality!")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
