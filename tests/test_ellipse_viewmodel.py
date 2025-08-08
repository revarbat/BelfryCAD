#!/usr/bin/env python3
"""
Test to verify refactored EllipseViewModel functionality.
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
from ellipse_viewmodel import EllipseViewModel

# Import the models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'models', 'cad_objects'))
from ellipse_cad_object import EllipseCadObject

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


class EllipseViewModelTest(QMainWindow):
    """Test widget to verify refactored EllipseViewModel functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EllipseViewModel Test")
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
        
        # Create an ellipse CAD object
        center_point = Point2D(0, 0)
        major_axis_point = Point2D(50, 0)  # Major axis to the right
        minor_axis_point = Point2D(0, 30)  # Minor axis up
        
        self.ellipse_object = EllipseCadObject(
            center_point=center_point,
            major_axis_point=major_axis_point,
            minor_axis_point=minor_axis_point,
            color="green",
            line_width=2.0
        )
        
        # Create ellipse viewmodel
        self.ellipse_viewmodel = EllipseViewModel(self.main_window, self.ellipse_object)
        
        # Test buttons
        self.test_properties_button = QPushButton("Test Ellipse Properties")
        self.test_properties_button.clicked.connect(self.test_ellipse_properties)
        layout.addWidget(self.test_properties_button)
        
        self.test_view_button = QPushButton("Test View Methods")
        self.test_view_button.clicked.connect(self.test_view_methods)
        layout.addWidget(self.test_view_button)
        
        self.test_transformations_button = QPushButton("Test Transformations")
        self.test_transformations_button.clicked.connect(self.test_transformations)
        layout.addWidget(self.test_transformations_button)
        
        # Set up the view
        self.view.setSceneRect(-100, -100, 200, 200)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("EllipseViewModel Test")
        print("Click buttons to test ellipse functionality")

    def test_ellipse_properties(self):
        """Test that ellipse properties work correctly."""
        print(f"Object ID: {self.ellipse_viewmodel.object_id}")
        print(f"Object Type: {self.ellipse_viewmodel.object_type}")
        print(f"Is Selected: {self.ellipse_viewmodel.is_selected}")
        print(f"Is Visible: {self.ellipse_viewmodel.is_visible}")
        print(f"Is Locked: {self.ellipse_viewmodel.is_locked}")
        print(f"Color: {self.ellipse_viewmodel.color}")
        print(f"Line Width: {self.ellipse_viewmodel.line_width}")
        
        # Test ellipse-specific properties
        print(f"Center Point: {self.ellipse_viewmodel.center_point}")
        print(f"Major Axis Point: {self.ellipse_viewmodel.major_axis_point}")
        print(f"Minor Axis Point: {self.ellipse_viewmodel.minor_axis_point}")
        print(f"Major Axis: {self.ellipse_viewmodel.major_axis}")
        print(f"Minor Axis: {self.ellipse_viewmodel.minor_axis}")
        print(f"Rotation: {math.degrees(self.ellipse_viewmodel.rotation)}°")
        print(f"Focus 1: {self.ellipse_viewmodel.focus1}")
        print(f"Focus 2: {self.ellipse_viewmodel.focus2}")
        
        # Test property changes
        print(f"Before major axis change: {self.ellipse_viewmodel.major_axis}")
        self.ellipse_viewmodel.major_axis = 75.0
        print(f"After major axis change: {self.ellipse_viewmodel.major_axis}")
        
        print(f"Before center change: {self.ellipse_viewmodel.center_point}")
        self.ellipse_viewmodel.center_point = QPointF(25, 25)
        print(f"After center change: {self.ellipse_viewmodel.center_point}")

    def test_view_methods(self):
        """Test that view methods work correctly."""
        print("Testing view methods...")
        
        # Test update_view
        self.ellipse_viewmodel.update_view(self.scene)
        print(f"View items created: {len(self.ellipse_viewmodel.view_items)}")
        
        # Test show/hide decorations
        self.ellipse_viewmodel.show_decorations(self.scene)
        print(f"Decorations shown: {len(self.ellipse_viewmodel.decorations)}")
        
        self.ellipse_viewmodel.hide_decorations(self.scene)
        print(f"Decorations hidden: {len(self.ellipse_viewmodel.decorations)}")
        
        # Test show/hide controls
        self.ellipse_viewmodel.show_controls(self.scene)
        print(f"Controls shown: {len(self.ellipse_viewmodel.controls)}")
        print("Should see 6 controls: 3 control points + 3 datums")
        
        self.ellipse_viewmodel.hide_controls(self.scene)
        print(f"Controls hidden: {len(self.ellipse_viewmodel.controls)}")

    def test_transformations(self):
        """Test transformation methods."""
        print("Testing transformations...")
        
        # Test translate
        print(f"Before translate - Center: {self.ellipse_viewmodel.center_point}")
        self.ellipse_viewmodel.translate(10, 20)
        print(f"After translate - Center: {self.ellipse_viewmodel.center_point}")
        
        # Test scale
        print(f"Before scale - Major Axis: {self.ellipse_viewmodel.major_axis}")
        self.ellipse_viewmodel.scale(1.5, QPointF(0, 0))
        print(f"After scale - Major Axis: {self.ellipse_viewmodel.major_axis}")
        
        # Test rotate
        print(f"Before rotate - Rotation: {math.degrees(self.ellipse_viewmodel.rotation)}°")
        self.ellipse_viewmodel.rotate(45, QPointF(0, 0))
        print(f"After rotate - Rotation: {math.degrees(self.ellipse_viewmodel.rotation)}°")
        
        # Test bounds
        bounds = self.ellipse_viewmodel.get_bounds()
        print(f"Bounds: {bounds}")
        
        # Test contains_point
        contains = self.ellipse_viewmodel.contains_point(QPointF(0, 0))
        print(f"Contains center point: {contains}")


def main():
    """Run the ellipse viewmodel test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = EllipseViewModelTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 