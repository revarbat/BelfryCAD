#!/usr/bin/env python3
"""
Test to verify refactored CircleViewModel functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

# Import the viewmodels
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'gui', 'viewmodels'))
from circle_viewmodel import CircleViewModel

# Import the models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'models', 'cad_objects'))
from circle_cad_object import CircleCadObject

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


class CircleViewModelTest(QMainWindow):
    """Test widget to verify refactored CircleViewModel functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CircleViewModel Test")
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
        
        # Create a circle CAD object
        center_point = Point2D(0, 0)
        radius = 50.0
        self.circle_object = CircleCadObject(
            center_point=center_point,
            perimeter_point=center_point + Point2D(radius, 0),
            color="red",
            line_width=2.0
        )
        
        # Create circle viewmodel
        self.circle_viewmodel = CircleViewModel(self.main_window, self.circle_object)
        
        # Test buttons
        self.test_properties_button = QPushButton("Test Circle Properties")
        self.test_properties_button.clicked.connect(self.test_circle_properties)
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
        
        print("CircleViewModel Test")
        print("Click buttons to test circle functionality")

    def test_circle_properties(self):
        """Test that circle properties work correctly."""
        print(f"Object ID: {self.circle_viewmodel.object_id}")
        print(f"Object Type: {self.circle_viewmodel.object_type}")
        print(f"Is Selected: {self.circle_viewmodel.is_selected}")
        print(f"Is Visible: {self.circle_viewmodel.is_visible}")
        print(f"Is Locked: {self.circle_viewmodel.is_locked}")
        print(f"Color: {self.circle_viewmodel.color}")
        print(f"Line Width: {self.circle_viewmodel.line_width}")
        
        # Test circle-specific properties
        print(f"Center Point: {self.circle_viewmodel.center_point}")
        print(f"Radius: {self.circle_viewmodel.radius}")
        print(f"Diameter: {self.circle_viewmodel.diameter}")
        print(f"Perimeter Point: {self.circle_viewmodel.perimeter_point}")
        
        # Test property changes
        print(f"Before radius change: {self.circle_viewmodel.radius}")
        self.circle_viewmodel.radius = 75.0
        print(f"After radius change: {self.circle_viewmodel.radius}")
        
        print(f"Before center change: {self.circle_viewmodel.center_point}")
        self.circle_viewmodel.center_point = QPointF(25, 25)
        print(f"After center change: {self.circle_viewmodel.center_point}")

    def test_view_methods(self):
        """Test that view methods work correctly."""
        print("Testing view methods...")
        
        # Test update_view
        self.circle_viewmodel.update_view(self.scene)
        print(f"View items created: {len(self.circle_viewmodel.view_items)}")
        
        # Test show/hide decorations
        self.circle_viewmodel.show_decorations(self.scene)
        print(f"Decorations shown: {len(self.circle_viewmodel.decorations)}")
        
        self.circle_viewmodel.hide_decorations(self.scene)
        print(f"Decorations hidden: {len(self.circle_viewmodel.decorations)}")
        
        # Test show/hide controls
        self.circle_viewmodel.show_controls(self.scene)
        print(f"Controls shown: {len(self.circle_viewmodel.controls)}")
        
        self.circle_viewmodel.hide_controls(self.scene)
        print(f"Controls hidden: {len(self.circle_viewmodel.controls)}")

    def test_transformations(self):
        """Test transformation methods."""
        print("Testing transformations...")
        
        # Test translate
        print(f"Before translate - Center: {self.circle_viewmodel.center_point}")
        self.circle_viewmodel.translate(10, 20)
        print(f"After translate - Center: {self.circle_viewmodel.center_point}")
        
        # Test scale
        print(f"Before scale - Radius: {self.circle_viewmodel.radius}")
        self.circle_viewmodel.scale(1.5, QPointF(0, 0))
        print(f"After scale - Radius: {self.circle_viewmodel.radius}")
        
        # Test rotate
        print(f"Before rotate - Center: {self.circle_viewmodel.center_point}")
        self.circle_viewmodel.rotate(45, QPointF(0, 0))
        print(f"After rotate - Center: {self.circle_viewmodel.center_point}")
        
        # Test bounds
        bounds = self.circle_viewmodel.get_bounds()
        print(f"Bounds: {bounds}")
        
        # Test contains_point
        contains = self.circle_viewmodel.contains_point(QPointF(0, 0))
        print(f"Contains center point: {contains}")


def main():
    """Run the circle viewmodel test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = CircleViewModelTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 