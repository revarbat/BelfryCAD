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
    mock_window = MockDocumentWindow()
    mock_document = Document()
    ellipse_obj = EllipseCadObject(mock_document, Point2D(0, 0), 10.0, 5.0, 0.0)
    ellipse_vm = EllipseViewModel(mock_window, ellipse_obj)
    datum = ControlDatum(
        model_view=ellipse_vm,
        setter=lambda x: None,
        label="Test Datum",
        format_string="{:.2f}",
        prefix="Test: ",
        suffix=" units"
    )
    assert datum is not None


def test_control_datum_paint():
    """Test that ControlDatum paint method doesn't crash."""
    from PySide6.QtGui import QPainter, QPixmap
    mock_window = MockDocumentWindow()
    mock_document = Document()
    ellipse_obj = EllipseCadObject(mock_document, Point2D(0, 0), 10.0, 5.0, 0.0)
    ellipse_vm = EllipseViewModel(mock_window, ellipse_obj)
    datum = ControlDatum(
        model_view=ellipse_vm,
        setter=lambda x: None,
        label="Test Datum",
        format_string="{:.2f}",
        prefix="Test: ",
        suffix=" units"
    )
    pixmap = QPixmap(100, 100)
    painter = QPainter(pixmap)
    datum.paint(painter, None, None)
    painter.end()


def test_control_datum_update():
    """Test that ControlDatum update_datum method doesn't crash."""
    mock_window = MockDocumentWindow()
    mock_document = Document()
    ellipse_obj = EllipseCadObject(mock_document, Point2D(0, 0), 10.0, 5.0, 0.0)
    ellipse_vm = EllipseViewModel(mock_window, ellipse_obj)
    datum = ControlDatum(
        model_view=ellipse_vm,
        setter=lambda x: None,
        label="Test Datum",
        format_string="{:.2f}",
        prefix="Test: ",
        suffix=" units"
    )
    datum.update_datum(42.5, QPointF(10, 10))


def test_viewmodel_controls():
    """Test that viewmodel controls can be created without crashing."""
    mock_window = MockDocumentWindow()
    mock_document = Document()
    ellipse_obj = EllipseCadObject(mock_document, Point2D(0, 0), 10.0, 5.0, 0.0)
    ellipse_vm = EllipseViewModel(mock_window, ellipse_obj)
    scene = QGraphicsScene()
    ellipse_vm.show_controls(scene)
    ellipse_vm.update_controls(scene)
    ellipse_vm.hide_controls(scene)


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