#!/usr/bin/env python3
"""
Test to verify that control point management has been moved to the viewmodel.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

# Import the factory and viewmodel
from BelfryCAD.gui.viewmodels.cad_object_factory import CADObjectFactory
from BelfryCAD.utils.geometry import Point2D


class LineViewModelControlPointsTest(QMainWindow):
    """Test widget to verify control point management in viewmodel."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Line ViewModel Control Points Test")
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
        
        # Create factory
        self.factory = CADObjectFactory()
        
        # Create line object with MVVM structure
        start_point = Point2D(0, 0)
        end_point = Point2D(100, 50)
        
        self.model, self.viewmodel, self.cad_item = self.factory.create_line_object(
            start_point=start_point,
            end_point=end_point,
            color="red",
            line_width=2.0
        )
        
        # Add CAD item to scene
        self.scene.addItem(self.cad_item)
        
        # Test buttons
        self.test_button = QPushButton("Test Control Points")
        self.test_button.clicked.connect(self.test_control_points)
        layout.addWidget(self.test_button)
        
        self.move_button = QPushButton("Move Line")
        self.move_button.clicked.connect(self.move_line)
        layout.addWidget(self.move_button)
        
        self.select_button = QPushButton("Select Line")
        self.select_button.clicked.connect(self.select_line)
        layout.addWidget(self.select_button)
        
        # Set up the view
        self.view.setSceneRect(-50, -50, 200, 150)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("Line ViewModel Control Points Test")
        print("Red line should be visible")
        print("Click 'Test Control Points' to check viewmodel control points")
        print("Click 'Move Line' to test movement")
        print("Click 'Select Line' to test selection")

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

    def select_line(self):
        """Test selecting the line."""
        print("Selecting line...")
        self.cad_item.setSelected(True)
        print("Line selected")


def main():
    """Run the line viewmodel control points test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = LineViewModelControlPointsTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 