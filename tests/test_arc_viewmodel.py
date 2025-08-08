#!/usr/bin/env python3
"""
Test to verify refactored ArcViewModel functionality with CadArcGraphicsItem and decoration arc.
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
from arc_viewmodel import ArcViewModel

# Import the models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'models', 'cad_objects'))
from arc_cad_object import ArcCadObject

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


class ArcViewModelTest(QMainWindow):
    """Test widget to verify refactored ArcViewModel functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ArcViewModel Test - CadArcGraphicsItem + Decoration Arc")
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
        
        # Create an arc CAD object
        center_point = Point2D(0, 0)
        radius = 50.0
        start_angle = 0.0  # Start at 0 degrees (right)
        span_angle = math.pi / 2  # 90 degrees span
        start_point = Point2D(center_point.x + radius, center_point.y)
        end_point = Point2D(center_point.x, center_point.y + radius)
        
        self.arc_object = ArcCadObject(
            center_point=center_point,
            start_point=start_point,
            end_point=end_point,
            color="blue",
            line_width=2.0
        )
        
        # Create arc viewmodel
        self.arc_viewmodel = ArcViewModel(self.main_window, self.arc_object)
        
        # Test buttons
        self.test_properties_button = QPushButton("Test Arc Properties")
        self.test_properties_button.clicked.connect(self.test_arc_properties)
        layout.addWidget(self.test_properties_button)
        
        self.test_view_button = QPushButton("Test View Methods (CadArcGraphicsItem + Decoration Arc)")
        self.test_view_button.clicked.connect(self.test_view_methods)
        layout.addWidget(self.test_view_button)
        
        self.test_transformations_button = QPushButton("Test Transformations")
        self.test_transformations_button.clicked.connect(self.test_transformations)
        layout.addWidget(self.test_transformations_button)
        
        # Set up the view
        self.view.setSceneRect(-100, -100, 200, 200)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("ArcViewModel Test - CadArcGraphicsItem + Decoration Arc")
        print("Click buttons to test arc functionality")
        print("Should see: Blue arc + Gray dashed decoration arc (when selected)")

    def test_arc_properties(self):
        """Test that arc properties work correctly."""
        print(f"Object ID: {self.arc_viewmodel.object_id}")
        print(f"Object Type: {self.arc_viewmodel.object_type}")
        print(f"Is Selected: {self.arc_viewmodel.is_selected}")
        print(f"Is Visible: {self.arc_viewmodel.is_visible}")
        print(f"Is Locked: {self.arc_viewmodel.is_locked}")
        print(f"Color: {self.arc_viewmodel.color}")
        print(f"Line Width: {self.arc_viewmodel.line_width}")
        
        # Test arc-specific properties
        print(f"Center Point: {self.arc_viewmodel.center_point}")
        print(f"Start Point: {self.arc_viewmodel.start_point}")
        print(f"End Point: {self.arc_viewmodel.end_point}")
        print(f"Radius: {self.arc_viewmodel.radius}")
        print(f"Start Angle: {math.degrees(self.arc_viewmodel.start_angle)}°")
        print(f"End Angle: {math.degrees(self.arc_viewmodel.end_angle)}°")
        print(f"Span Angle: {math.degrees(self.arc_viewmodel.span_angle)}°")
        
        # Test property changes
        print(f"Before radius change: {self.arc_viewmodel.radius}")
        self.arc_viewmodel.radius = 75.0
        print(f"After radius change: {self.arc_viewmodel.radius}")
        
        print(f"Before center change: {self.arc_viewmodel.center_point}")
        self.arc_viewmodel.center_point = QPointF(25, 25)
        print(f"After center change: {self.arc_viewmodel.center_point}")

    def test_view_methods(self):
        """Test that view methods work correctly."""
        print("Testing view methods...")
        print("Should create CadArcGraphicsItem in update_view()")
        
        # Test update_view
        self.arc_viewmodel.update_view(self.scene)
        print(f"View items created: {len(self.arc_viewmodel.view_items)}")
        print("Should see 1 item: CadArcGraphicsItem (blue arc)")
        
        # Test show/hide decorations
        self.arc_viewmodel.show_decorations(self.scene)
        print(f"Decorations shown: {len(self.arc_viewmodel.decorations)}")
        print("Should see 1 decoration: Decoration Arc (gray dashed) completing the circle")
        
        self.arc_viewmodel.hide_decorations(self.scene)
        print(f"Decorations hidden: {len(self.arc_viewmodel.decorations)}")
        
        # Test show/hide controls
        self.arc_viewmodel.show_controls(self.scene)
        print(f"Controls shown: {len(self.arc_viewmodel.controls)}")
        print("Should see 5 controls: 3 control points + 2 datums")
        
        self.arc_viewmodel.hide_controls(self.scene)
        print(f"Controls hidden: {len(self.arc_viewmodel.controls)}")

    def test_transformations(self):
        """Test transformation methods."""
        print("Testing transformations...")
        
        # Test translate
        print(f"Before translate - Center: {self.arc_viewmodel.center_point}")
        self.arc_viewmodel.translate(10, 20)
        print(f"After translate - Center: {self.arc_viewmodel.center_point}")
        
        # Test scale
        print(f"Before scale - Radius: {self.arc_viewmodel.radius}")
        self.arc_viewmodel.scale(1.5, QPointF(0, 0))
        print(f"After scale - Radius: {self.arc_viewmodel.radius}")
        
        # Test rotate
        print(f"Before rotate - Start Angle: {math.degrees(self.arc_viewmodel.start_angle)}°")
        self.arc_viewmodel.rotate(45, QPointF(0, 0))
        print(f"After rotate - Start Angle: {math.degrees(self.arc_viewmodel.start_angle)}°")
        
        # Test bounds
        bounds = self.arc_viewmodel.get_bounds()
        print(f"Bounds: {bounds}")
        
        # Test contains_point
        contains = self.arc_viewmodel.contains_point(QPointF(0, 0))
        print(f"Contains center point: {contains}")


def main():
    """Run the arc viewmodel test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = ArcViewModelTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 