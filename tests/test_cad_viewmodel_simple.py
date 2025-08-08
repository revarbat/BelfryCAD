#!/usr/bin/env python3
"""
Simple test to verify CadViewModel base class functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the CadViewModel first
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'BelfryCAD', 'gui', 'viewmodels'))
from cad_viewmodel import CadViewModel

from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtWidgets import QGraphicsScene


class MockCADObject:
    """Mock CAD object for testing."""
    
    def __init__(self):
        self.object_id = "test_object"
        self.visible = True
        self.locked = False
        self.color = "red"


class MockMainWindow:
    """Mock main window for testing."""
    
    def __init__(self):
        self.preferences_viewmodel = MockPreferencesViewModel()


class MockPreferencesViewModel:
    """Mock preferences viewmodel for testing."""
    
    def get_precision(self):
        return 3


class TestCadViewModel(CadViewModel):
    """Test implementation of CadViewModel."""
    
    def update_view(self, scene):
        print("update_view called")
    
    def show_decorations(self, scene):
        print("show_decorations called")
    
    def hide_decorations(self, scene):
        print("hide_decorations called")
    
    def update_decorations(self, scene):
        print("update_decorations called")
    
    def show_controls(self, scene):
        print("show_controls called")
    
    def hide_controls(self, scene):
        print("hide_controls called")
    
    def update_controls(self, scene):
        print("update_controls called")
    
    def get_bounds(self):
        return (0, 0, 100, 100)
    
    def contains_point(self, point, tolerance=5.0):
        return True
    
    @property
    def object_type(self):
        return "test"


def test_cad_viewmodel():
    """Test the CadViewModel base class."""
    print("Testing CadViewModel base class...")
    
    # Create mock objects
    main_window = MockMainWindow()
    cad_object = MockCADObject()
    
    # Create test viewmodel
    viewmodel = TestCadViewModel(main_window, cad_object)
    
    # Test base properties
    print(f"Object ID: {viewmodel.object_id}")
    print(f"Object Type: {viewmodel.object_type}")
    print(f"Is Selected: {viewmodel.is_selected}")
    print(f"Is Visible: {viewmodel.is_visible}")
    print(f"Is Locked: {viewmodel.is_locked}")
    print(f"Color: {viewmodel.color}")
    
    # Test selection
    print(f"Before selection: {viewmodel.is_selected}")
    viewmodel.is_selected = True
    print(f"After selection: {viewmodel.is_selected}")
    
    # Test color change
    print(f"Before color change: {viewmodel.color}")
    viewmodel.color = "blue"
    print(f"After color change: {viewmodel.color}")
    
    # Test helper methods
    scene = QGraphicsScene()
    viewmodel._clear_view_items(scene)
    viewmodel._add_view_items_to_scene(scene)
    viewmodel._clear_decorations(scene)
    viewmodel._add_decorations_to_scene(scene)
    viewmodel._clear_controls(scene)
    viewmodel._add_controls_to_scene(scene)
    
    # Test abstract methods
    viewmodel.update_view(scene)
    viewmodel.show_decorations(scene)
    viewmodel.hide_decorations(scene)
    viewmodel.update_decorations(scene)
    viewmodel.show_controls(scene)
    viewmodel.hide_controls(scene)
    viewmodel.update_controls(scene)
    
    bounds = viewmodel.get_bounds()
    print(f"Bounds: {bounds}")
    
    contains = viewmodel.contains_point(QPointF(50, 50))
    print(f"Contains point: {contains}")
    
    print("All tests passed!")


if __name__ == "__main__":
    test_cad_viewmodel() 