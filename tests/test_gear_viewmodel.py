#!/usr/bin/env python3
"""
Test to verify refactored GearViewModel functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
import math

# Import the viewmodels using absolute imports
from BelfryCAD.gui.viewmodels.gear_viewmodel import GearViewModel

# Import the models using absolute imports
from BelfryCAD.models.cad_objects.gear_cad_object import GearCadObject

# Import geometry using absolute imports
from BelfryCAD.utils.geometry import Point2D


class MockMainWindow:
    """Mock main window for testing."""
    
    def __init__(self):
        self.preferences_viewmodel = MockPreferencesViewModel()


class MockPreferencesViewModel:
    """Mock preferences viewmodel for testing."""
    
    def get_precision(self):
        return 3


class GearViewModelTest(QMainWindow):
    """Test widget to verify refactored GearViewModel functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GearViewModel Test")
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
        
        # Create a gear CAD object
        self.gear_object = GearCadObject(
            center_point=Point2D(0, 0),
            pitch_diameter=2.0,
            num_teeth=20,
            pressure_angle=20.0,
            color="blue",
            line_width=2.0
        )
        
        # Create gear viewmodel
        self.gear_viewmodel = GearViewModel(self.main_window, self.gear_object)
        
        # Test buttons
        self.test_properties_button = QPushButton("Test Gear Properties")
        self.test_properties_button.clicked.connect(self.test_gear_properties)
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
        
        print("GearViewModel Test")
        print("Click buttons to test gear functionality")

    def test_gear_properties(self):
        """Test that gear properties work correctly."""
        print(f"Object ID: {self.gear_viewmodel.object_id}")
        print(f"Object Type: {self.gear_viewmodel.object_type}")
        print(f"Is Selected: {self.gear_viewmodel.is_selected}")
        print(f"Is Visible: {self.gear_viewmodel.is_visible}")
        print(f"Is Locked: {self.gear_viewmodel.is_locked}")
        print(f"Color: {self.gear_viewmodel.color}")
        print(f"Line Width: {self.gear_viewmodel.line_width}")
        
        # Test gear-specific properties
        print(f"Center Point: {self.gear_viewmodel.center_point}")
        print(f"Pitch Diameter: {self.gear_viewmodel.pitch_diameter}")
        print(f"Number of Teeth: {self.gear_viewmodel.num_teeth}")
        print(f"Pressure Angle: {self.gear_viewmodel.pressure_angle}")
        print(f"Pitch Radius: {self.gear_viewmodel.pitch_radius}")
        print(f"Module: {self.gear_viewmodel.module}")
        print(f"Diametral Pitch: {self.gear_viewmodel.diametral_pitch}")
        print(f"Circular Pitch: {self.gear_viewmodel.circular_pitch}")
        
        # Test property changes
        print(f"Before changing center point")
        self.gear_viewmodel.center_point = QPointF(10, 10)
        print(f"After changing center point: {self.gear_viewmodel.center_point}")
        
        print(f"Before changing pitch diameter")
        self.gear_viewmodel.pitch_diameter = 3.0
        print(f"After changing pitch diameter: {self.gear_viewmodel.pitch_diameter}")

    def test_view_methods(self):
        """Test that view methods work correctly."""
        print("Testing view methods...")
        
        # Test update_view
        self.gear_viewmodel.update_view(self.scene)
        print(f"View items created: {len(self.gear_viewmodel.view_items)}")
        
        # Test show/hide decorations
        self.gear_viewmodel.show_decorations(self.scene)
        print(f"Decorations shown: {len(self.gear_viewmodel.decorations)}")
        
        self.gear_viewmodel.hide_decorations(self.scene)
        print(f"Decorations hidden: {len(self.gear_viewmodel.decorations)}")
        
        # Test show/hide controls
        self.gear_viewmodel.show_controls(self.scene)
        print(f"Controls shown: {len(self.gear_viewmodel.controls)}")
        print(f"Should see 2 control points + 4 datums")
        
        self.gear_viewmodel.hide_controls(self.scene)
        print(f"Controls hidden: {len(self.gear_viewmodel.controls)}")

    def test_transformations(self):
        """Test transformation methods."""
        print("Testing transformations...")
        
        # Test translate
        print(f"Before translate - Center point: {self.gear_viewmodel.center_point}")
        self.gear_viewmodel.translate(10, 20)
        print(f"After translate - Center point: {self.gear_viewmodel.center_point}")
        
        # Test scale
        print(f"Before scale - Pitch diameter: {self.gear_viewmodel.pitch_diameter}")
        self.gear_viewmodel.scale(1.5, QPointF(0, 0))
        print(f"After scale - Pitch diameter: {self.gear_viewmodel.pitch_diameter}")
        
        # Test rotate
        print(f"Before rotate - Center point: {self.gear_viewmodel.center_point}")
        self.gear_viewmodel.rotate(45, QPointF(0, 0))
        print(f"After rotate - Center point: {self.gear_viewmodel.center_point}")
        
        # Test bounds
        bounds = self.gear_viewmodel.get_bounds()
        print(f"Bounds: {bounds}")
        
        # Test contains_point
        contains = self.gear_viewmodel.contains_point(QPointF(0, 0))
        print(f"Contains center point: {contains}")
        
        # Test gear path points
        gear_points = self.gear_viewmodel.get_gear_path_points()
        print(f"Gear path points: {len(gear_points)} points")
        
        # Test pitch circle points
        pitch_points = self.gear_viewmodel.get_pitch_circle_points()
        print(f"Pitch circle points: {len(pitch_points)} points")


def main():
    """Run the gear viewmodel test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = GearViewModelTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 