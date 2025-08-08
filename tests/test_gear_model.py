#!/usr/bin/env python3
"""
Test to verify that GearCadObject correctly uses the SpurGear class.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPen, QBrush
import math

# Import the models using absolute imports
from BelfryCAD.models.cad_objects.gear_cad_object import GearCadObject

# Import geometry using absolute imports
from BelfryCAD.utils.geometry import Point2D


class GearModelTest(QMainWindow):
    """Test widget to verify GearCadObject functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gear Model Test")
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
        
        # Create a gear CAD object
        self.gear_object = GearCadObject(
            center_point=Point2D(0, 0),
            pitch_diameter=10.0,  # Increased from 2.0 to 10.0
            num_teeth=20,
            pressure_angle=20.0,
            color="blue",
            line_width=2.0
        )
        
        # Test buttons
        self.test_properties_button = QPushButton("Test Gear Properties")
        self.test_properties_button.clicked.connect(self.test_gear_properties)
        layout.addWidget(self.test_properties_button)
        
        self.test_geometry_button = QPushButton("Test Gear Geometry")
        self.test_geometry_button.clicked.connect(self.test_gear_geometry)
        layout.addWidget(self.test_geometry_button)
        
        self.draw_gear_button = QPushButton("Draw Gear")
        self.draw_gear_button.clicked.connect(self.draw_gear)
        layout.addWidget(self.draw_gear_button)
        
        # Set up the view
        self.view.setSceneRect(-100, -100, 400, 200)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("Gear Model Test")
        print("Click buttons to test gear functionality")

    def test_gear_properties(self):
        """Test that gear properties work correctly."""
        print(f"Center Point: {self.gear_object.center_point}")
        print(f"Pitch Diameter: {self.gear_object.pitch_diameter}")
        print(f"Number of Teeth: {self.gear_object.num_teeth}")
        print(f"Pressure Angle: {self.gear_object.pressure_angle}")
        print(f"Pitch Radius: {self.gear_object.pitch_radius}")
        print(f"Module: {self.gear_object.module}")
        print(f"Diametral Pitch: {self.gear_object.diametral_pitch}")
        print(f"Circular Pitch: {self.gear_object.circular_pitch}")
        
        # Test property changes
        print(f"Before changing center point")
        self.gear_object.center_point = Point2D(50, 50)  # Increased from (10, 10) to (50, 50)
        print(f"After changing center point: {self.gear_object.center_point}")
        
        print(f"Before changing pitch diameter")
        self.gear_object.pitch_diameter = 15.0  # Increased from 3.0 to 15.0
        print(f"After changing pitch diameter: {self.gear_object.pitch_diameter}")

    def test_gear_geometry(self):
        """Test that gear geometry methods work correctly."""
        print("Testing gear geometry...")
        
        # Test gear path points
        gear_points = self.gear_object.get_gear_path_points()
        print(f"Gear path points: {len(gear_points)} points")
        if gear_points:
            print(f"First point: {gear_points[0]}")
            print(f"Last point: {gear_points[-1]}")
        
        # Test pitch circle points
        pitch_points = self.gear_object.get_pitch_circle_points()
        print(f"Pitch circle points: {len(pitch_points)} points")
        if pitch_points:
            print(f"First point: {pitch_points[0]}")
            print(f"Last point: {pitch_points[-1]}")
        
        # Test bounds
        bounds = self.gear_object.get_bounds()
        print(f"Bounds: {bounds}")

    def draw_gear(self):
        """Draw the gear in the graphics scene."""
        print("Drawing gear...")
        
        # Clear the scene
        self.scene.clear()
        
        # Get gear path points
        gear_points = self.gear_object.get_gear_path_points()
        
        if gear_points:
            # Create a polygon from the gear points
            from PySide6.QtGui import QPolygonF
            polygon = QPolygonF()
            for point in gear_points:
                polygon.append(QPointF(point.x, point.y))
            
            # Create a graphics item for the gear
            from PySide6.QtWidgets import QGraphicsPolygonItem
            gear_item = QGraphicsPolygonItem(polygon)
            gear_item.setPen(QPen(QColor("blue"), 2))
            gear_item.setBrush(QBrush(QColor("lightblue")))
            self.scene.addItem(gear_item)
            
            # Draw pitch circle
            pitch_points = self.gear_object.get_pitch_circle_points()
            if pitch_points:
                pitch_polygon = QPolygonF()
                for point in pitch_points:
                    pitch_polygon.append(QPointF(point.x, point.y))
                
                pitch_item = QGraphicsPolygonItem(pitch_polygon)
                pitch_item.setPen(QPen(QColor("red"), 1, Qt.PenStyle.DashLine))
                pitch_item.setBrush(QBrush(QColor("transparent")))
                self.scene.addItem(pitch_item)
            
            print("Gear drawn!")
        else:
            print("No gear points to draw")


def main():
    """Run the gear model test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = GearModelTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 