#!/usr/bin/env python3
"""
Test to verify refactored CubicBezierViewModel functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
import math

# Import the viewmodels
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'gui', 'viewmodels'))
from cubic_bezier_viewmodel import CubicBezierViewModel

# Import the models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'models', 'cad_objects'))
from cubic_bezier_cad_object import CubicBezierCadObject

# Import geometry
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'utils'))
from geometry import Point2D


class MockMainWindow:
    """Mock main window for testing."""
    
    def __init__(self):
        self.preferences_viewmodel = MockPreferencesViewModel()


class MockPreferencesViewModel:
    """Mock preferences viewmodel for testing."""
    
    def get_precision(self):
        return 3


class CubicBezierViewModelTest(QMainWindow):
    """Test widget to verify refactored CubicBezierViewModel functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CubicBezierViewModel Test")
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
        
        # Create mock main window
        self.main_window = MockMainWindow()
        
        # Create a cubic Bezier CAD object with 7 points (2 cubic segments)
        points = [
            Point2D(0, 0),      # Start point
            Point2D(20, 20),    # Control point 1
            Point2D(40, -10),   # Control point 2
            Point2D(60, 30),    # End point / Start of next segment
            Point2D(80, 10),    # Control point 1
            Point2D(100, 40),   # Control point 2
            Point2D(120, 20),   # End point
        ]
        
        self.bezier_object = CubicBezierCadObject(
            points=points,
            color="purple",
            line_width=2.0
        )
        
        # Create Bezier viewmodel
        self.bezier_viewmodel = CubicBezierViewModel(self.main_window, self.bezier_object)
        
        # Test buttons
        self.test_properties_button = QPushButton("Test Bezier Properties")
        self.test_properties_button.clicked.connect(self.test_bezier_properties)
        layout.addWidget(self.test_properties_button)
        
        self.test_view_button = QPushButton("Test View Methods")
        self.test_view_button.clicked.connect(self.test_view_methods)
        layout.addWidget(self.test_view_button)
        
        self.test_transformations_button = QPushButton("Test Transformations")
        self.test_transformations_button.clicked.connect(self.test_transformations)
        layout.addWidget(self.test_transformations_button)
        
        # Set up the view
        self.view.setSceneRect(-50, -50, 200, 100)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("CubicBezierViewModel Test")
        print("Click buttons to test Bezier curve functionality")

    def test_bezier_properties(self):
        """Test that Bezier properties work correctly."""
        print(f"Object ID: {self.bezier_viewmodel.object_id}")
        print(f"Object Type: {self.bezier_viewmodel.object_type}")
        print(f"Is Selected: {self.bezier_viewmodel.is_selected}")
        print(f"Is Visible: {self.bezier_viewmodel.is_visible}")
        print(f"Is Locked: {self.bezier_viewmodel.is_locked}")
        print(f"Color: {self.bezier_viewmodel.color}")
        print(f"Line Width: {self.bezier_viewmodel.line_width}")
        
        # Test Bezier-specific properties
        print(f"Points: {self.bezier_viewmodel.points}")
        print(f"Start Point: {self.bezier_viewmodel.start_point}")
        print(f"End Point: {self.bezier_viewmodel.end_point}")
        print(f"Is Closed: {self.bezier_viewmodel.is_closed}")
        
        # Test property changes
        print(f"Before adding point")
        self.bezier_viewmodel.add_point(QPointF(140, 0))
        print(f"After adding point: {len(self.bezier_viewmodel.points)} points")
        
        print(f"Before setting point")
        self.bezier_viewmodel.set_point(0, QPointF(10, 10))
        print(f"After setting point: {self.bezier_viewmodel.get_point(0)}")

    def test_view_methods(self):
        """Test that view methods work correctly."""
        print("Testing view methods...")
        
        # Test update_view
        self.bezier_viewmodel.update_view(self.scene)
        print(f"View items created: {len(self.bezier_viewmodel.view_items)}")
        
        # Test show/hide decorations
        self.bezier_viewmodel.show_decorations(self.scene)
        print(f"Decorations shown: {len(self.bezier_viewmodel.decorations)}")
        
        self.bezier_viewmodel.hide_decorations(self.scene)
        print(f"Decorations hidden: {len(self.bezier_viewmodel.decorations)}")
        
        # Test show/hide controls
        self.bezier_viewmodel.show_controls(self.scene)
        print(f"Controls shown: {len(self.bezier_viewmodel.controls)}")
        print(f"Should see {len(self.bezier_viewmodel.points)} control points + 2 datums")
        
        self.bezier_viewmodel.hide_controls(self.scene)
        print(f"Controls hidden: {len(self.bezier_viewmodel.controls)}")

    def test_transformations(self):
        """Test transformation methods."""
        print("Testing transformations...")
        
        # Test translate
        print(f"Before translate - Start point: {self.bezier_viewmodel.start_point}")
        self.bezier_viewmodel.translate(10, 20)
        print(f"After translate - Start point: {self.bezier_viewmodel.start_point}")
        
        # Test scale
        print(f"Before scale - Points: {len(self.bezier_viewmodel.points)}")
        self.bezier_viewmodel.scale(1.5, QPointF(0, 0))
        print(f"After scale - Points: {len(self.bezier_viewmodel.points)}")
        
        # Test rotate
        print(f"Before rotate - Points: {len(self.bezier_viewmodel.points)}")
        self.bezier_viewmodel.rotate(45, QPointF(0, 0))
        print(f"After rotate - Points: {len(self.bezier_viewmodel.points)}")
        
        # Test bounds
        bounds = self.bezier_viewmodel.get_bounds()
        print(f"Bounds: {bounds}")
        
        # Test contains_point
        contains = self.bezier_viewmodel.contains_point(QPointF(0, 0))
        print(f"Contains start point: {contains}")


def main():
    """Run the cubic Bezier viewmodel test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = CubicBezierViewModelTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 