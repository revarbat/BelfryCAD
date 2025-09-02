#!/usr/bin/env python3
"""
Test script to verify the crash fix for switching between CAD objects.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor

from BelfryCAD.gui.graphics_items.control_points import ControlDatum
from BelfryCAD.gui.viewmodels.cad_viewmodels.ellipse_viewmodel import EllipseViewModel
from BelfryCAD.gui.viewmodels.cad_viewmodels.arc_viewmodel import ArcViewModel
from BelfryCAD.models.cad_objects.ellipse_cad_object import EllipseCadObject
from BelfryCAD.models.cad_objects.arc_cad_object import ArcCadObject
from BelfryCAD.models.document import Document
from BelfryCAD.cad_geometry import Point2D


class MockDocumentWindow:
    """Mock document window for testing."""
    def __init__(self):
        self.grid_info = MockGridInfo()
        self.preferences_viewmodel = MockPreferencesViewModel()
        self.cad_scene = MockCadScene()
        self.cad_expression = None


class MockGridInfo:
    """Mock grid info for testing."""
    def format_label(self, value, no_subs=False):
        return f"{value:.3f}"


class MockPreferencesViewModel:
    """Mock preferences viewmodel for testing."""
    def get_precision(self):
        return 3


class MockCadScene:
    """Mock cad scene for testing."""
    def get_precision(self):
        return 3


def test_control_datum_initialization():
    """Test that ControlDatum can be initialized without crashing."""
    print("Testing ControlDatum initialization...")
    
    # Create mock objects
    mock_window = MockDocumentWindow()
    mock_document = Document()
    
    # Create a mock viewmodel
    ellipse_obj = EllipseCadObject(mock_document, Point2D(0, 0), 10.0, 5.0, 0.0)
    ellipse_vm = EllipseViewModel(mock_window, ellipse_obj)
    
    # Create a control datum
    try:
        datum = ControlDatum(
            model_view=ellipse_vm,
            setter=lambda x: None,
            label="Test Datum",
            format_string="{:.2f}",
            prefix="Test: ",
            suffix=" units"
        )
        print("✓ ControlDatum initialization successful")
        return True
    except Exception as e:
        print(f"✗ ControlDatum initialization failed: {e}")
        return False


def test_control_datum_paint():
    """Test that ControlDatum paint method doesn't crash."""
    print("Testing ControlDatum paint method...")
    
    # Create mock objects
    mock_window = MockDocumentWindow()
    mock_document = Document()
    
    # Create a mock viewmodel
    ellipse_obj = EllipseCadObject(mock_document, Point2D(0, 0), 10.0, 5.0, 0.0)
    ellipse_vm = EllipseViewModel(mock_window, ellipse_obj)
    
    # Create a control datum
    datum = ControlDatum(
        model_view=ellipse_vm,
        setter=lambda x: None,
        label="Test Datum",
        format_string="{:.2f}",
        prefix="Test: ",
        suffix=" units"
    )
    
    # Test paint method
    try:
        from PySide6.QtGui import QPainter, QPixmap
        pixmap = QPixmap(100, 100)
        painter = QPainter(pixmap)
        datum.paint(painter, None, None)
        painter.end()
        print("✓ ControlDatum paint method successful")
        return True
    except Exception as e:
        print(f"✗ ControlDatum paint method failed: {e}")
        return False


def test_control_datum_update():
    """Test that ControlDatum update_datum method doesn't crash."""
    print("Testing ControlDatum update_datum method...")
    
    # Create mock objects
    mock_window = MockDocumentWindow()
    mock_document = Document()
    
    # Create a mock viewmodel
    ellipse_obj = EllipseCadObject(mock_document, Point2D(0, 0), 10.0, 5.0, 0.0)
    ellipse_vm = EllipseViewModel(mock_window, ellipse_obj)
    
    # Create a control datum
    datum = ControlDatum(
        model_view=ellipse_vm,
        setter=lambda x: None,
        label="Test Datum",
        format_string="{:.2f}",
        prefix="Test: ",
        suffix=" units"
    )
    
    # Test update_datum method
    try:
        datum.update_datum(42.5, QPointF(10, 10))
        print("✓ ControlDatum update_datum method successful")
        return True
    except Exception as e:
        print(f"✗ ControlDatum update_datum method failed: {e}")
        return False


def test_viewmodel_controls():
    """Test that viewmodel controls can be created without crashing."""
    print("Testing viewmodel controls creation...")
    
    # Create mock objects
    mock_window = MockDocumentWindow()
    mock_document = Document()
    
    # Test ellipse viewmodel controls
    try:
        ellipse_obj = EllipseCadObject(mock_document, Point2D(0, 0), 10.0, 5.0, 0.0)
        ellipse_vm = EllipseViewModel(mock_window, ellipse_obj)
        
        # Create a mock scene
        scene = QGraphicsScene()
        
        # Test show_controls
        ellipse_vm.show_controls(scene)
        print("✓ Ellipse viewmodel show_controls successful")
        
        # Test update_controls
        ellipse_vm.update_controls(scene)
        print("✓ Ellipse viewmodel update_controls successful")
        
        # Test hide_controls
        ellipse_vm.hide_controls(scene)
        print("✓ Ellipse viewmodel hide_controls successful")
        
        return True
    except Exception as e:
        print(f"✗ Ellipse viewmodel controls failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=== Testing Crash Fix ===")
    
    # Create QApplication if needed
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Run tests
    tests = [
        test_control_datum_initialization,
        test_control_datum_paint,
        test_control_datum_update,
        test_viewmodel_controls
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Test Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("✓ All tests passed! The crash fix appears to be working.")
        return 0
    else:
        print("✗ Some tests failed. The crash fix may need more work.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 