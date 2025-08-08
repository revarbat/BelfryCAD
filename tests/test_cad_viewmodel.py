#!/usr/bin/env python3
"""
Test to verify CadViewModel base class functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen
from PySide6.QtCore import Qt

# Import the viewmodels
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'gui', 'viewmodels'))
from cad_viewmodel import CadViewModel
from line_viewmodel import LineViewModel

# Import the models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'models', 'cad_objects'))
from line_cad_object import LineCadObject

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


class CadViewModelTest(QMainWindow):
    """Test widget to verify CadViewModel base class functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CadViewModel Base Class Test")
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
        
        # Create a line CAD object
        start_point = Point2D(0, 0)
        end_point = Point2D(100, 50)
        self.line_object = LineCadObject(
            start_point=start_point,
            end_point=end_point,
            color="red",
            line_width=2.0
        )
        
        # Create line viewmodel
        self.line_viewmodel = LineViewModel(self.main_window, self.line_object)
        
        # Test buttons
        self.test_properties_button = QPushButton("Test Base Properties")
        self.test_properties_button.clicked.connect(self.test_base_properties)
        layout.addWidget(self.test_properties_button)
        
        self.test_view_button = QPushButton("Test View Methods")
        self.test_view_button.clicked.connect(self.test_view_methods)
        layout.addWidget(self.test_view_button)
        
        self.test_selection_button = QPushButton("Test Selection")
        self.test_selection_button.clicked.connect(self.test_selection)
        layout.addWidget(self.test_selection_button)
        
        # Set up the view
        self.view.setSceneRect(-50, -50, 200, 150)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)
        
        print("CadViewModel Base Class Test")
        print("Click buttons to test base class functionality")

    def test_base_properties(self):
        """Test that base properties work correctly."""
        print(f"Object ID: {self.line_viewmodel.object_id}")
        print(f"Object Type: {self.line_viewmodel.object_type}")
        print(f"Is Selected: {self.line_viewmodel.is_selected}")
        print(f"Is Visible: {self.line_viewmodel.is_visible}")
        print(f"Is Locked: {self.line_viewmodel.is_locked}")
        print(f"Color: {self.line_viewmodel.color}")
        
        # Test selection
        print(f"Before selection: {self.line_viewmodel.is_selected}")
        self.line_viewmodel.is_selected = True
        print(f"After selection: {self.line_viewmodel.is_selected}")
        
        # Test color change
        print(f"Before color change: {self.line_viewmodel.color}")
        self.line_viewmodel.color = "blue"
        print(f"After color change: {self.line_viewmodel.color}")

    def test_view_methods(self):
        """Test that view methods work correctly."""
        print("Testing view methods...")
        
        # Test update_view
        self.line_viewmodel.update_view(self.scene)
        print(f"View items created: {len(self.line_viewmodel.view_items)}")
        
        # Test show/hide decorations
        self.line_viewmodel.show_decorations(self.scene)
        print(f"Decorations shown: {len(self.line_viewmodel.decorations)}")
        
        self.line_viewmodel.hide_decorations(self.scene)
        print(f"Decorations hidden: {len(self.line_viewmodel.decorations)}")
        
        # Test show/hide controls
        self.line_viewmodel.show_controls(self.scene)
        print(f"Controls shown: {len(self.line_viewmodel.controls)}")
        
        self.line_viewmodel.hide_controls(self.scene)
        print(f"Controls hidden: {len(self.line_viewmodel.controls)}")

    def test_selection(self):
        """Test selection behavior."""
        print("Testing selection behavior...")
        
        # Test selection signals
        self.line_viewmodel.object_selected.connect(lambda selected: print(f"Selection changed: {selected}"))
        self.line_viewmodel.object_modified.connect(lambda: print("Object modified"))
        
        # Change selection
        self.line_viewmodel.is_selected = True
        self.line_viewmodel.is_selected = False


def main():
    """Run the CadViewModel base class test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    widget = CadViewModelTest()
    widget.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 