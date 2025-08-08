#!/usr/bin/env python3
"""
Simple test to verify that control point management has been moved to the viewmodel.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

# Import directly to avoid package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'gui', 'viewmodels'))
from line_viewmodel import LineViewModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'gui', 'views', 'graphics_items', 'caditems'))
from line_cad_item import LineCadItem

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'models', 'cad_objects'))
from line_cad_object import LineCadObject

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'utils'))
from geometry import Point2D


class SimpleLineViewModelTest(QMainWindow):
    """Simple test widget to verify control point management in viewmodel."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Line ViewModel Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create graphics view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)
        
        # Create model, viewmodel, and view directly
        start_point = Point2D(0, 0)
        end_point = Point2D(100, 50)
        
        # Create model
        self.model = LineCadObject(
            start_point=start_point,
            end_point=end_point,
            color="red",
            line_width=2.0
        )
        
        # Create viewmodel
        self.viewmodel = LineViewModel(self.model)
        
        # Create CAD item
        self.cad_item = LineCadItem(
            main_window=None,
            start_point=start_point.to_qpointf(),
            end_point=end_point.to_qpointf(),
            color=QColor(255, 0, 0),
            line_width=2.0
        )
        
        # Connect viewmodel to CAD item
        self.cad_item.set_viewmodel(self.viewmodel)
        
        # Add CAD item to scene
        self.scene.addItem(self.cad_item)
        
        # Test buttons
        self.test_button = QPushButton("Test Control Points")
        self.test_button.clicked.connect(self.test_control_points)
        layout.addWidget(self.test_button)
        
        self.move_button = QPushButton("Move Line")
        self.move_button.clicked.connect(self.move_line)
        layout.addWidget(self.move_button)
        
        # Set up the view
        self.view.setSceneRect(-50, -50, 200, 150)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("Simple Line ViewModel Test")
        print("Red line should be visible")
        print("Click 'Test Control Points' to check viewmodel control points")
        print("Click 'Move Line' to test movement")

    def test_control_points(self):
        """Test that control points are managed by the viewmodel."""
        print(f"CAD item has viewmodel: {hasattr(self.cad_item, 'viewmodel')}")
        print(f"Viewmodel exists: {self.cad_item.viewmodel is not None}")
        
        if self.cad_item.viewmodel:
            viewmodel = self.cad_item.viewmodel
            print(f"Viewmodel type: {type(viewmodel)}")
            print(f"Viewmodel has control points: {hasattr(viewmodel, 'get_control_points')}")
            print(f"Viewmodel has control datums: {hasattr(viewmodel, 'get_control_datums')}")
            
            # Test control point creation
            control_points = viewmodel.get_control_points()
            control_datums = viewmodel.get_control_datums()
            
            print(f"Control points count: {len(control_points)}")
            print(f"Control datums count: {len(control_datums)}")
            
            # Test that CAD item doesn't have old control point methods
            print(f"CAD item has _create_controls_impl: {hasattr(self.cad_item, '_create_controls_impl')}")
            print(f"CAD item has updateControls: {hasattr(self.cad_item, 'updateControls')}")
            
            # Test control point movement
            if len(control_points) > 0:
                print("Testing control point movement...")
                viewmodel.move_control_point(0, 10, 10)  # Move first control point
                print("Control point moved via viewmodel")
        
        print("Control point test completed")

    def move_line(self):
        """Test moving the line."""
        print("Moving line...")
        self.cad_item.moveBy(10, 10)
        print("Line moved")


def main():
    """Run the simple line viewmodel test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = SimpleLineViewModelTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 