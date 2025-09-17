#!/usr/bin/env python3
"""
Test script to verify RectangleViewModel uses CadPolygonGraphicsItem.

This script verifies that the RectangleViewModel creates CadPolygonGraphicsItem 
instances instead of CadRectangleGraphicsItem when rendering rectangles.
"""

import sys
import os

# Add the src directory to the path so we can import BelfryCAD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication

from BelfryCAD.models.document import Document
from BelfryCAD.models.cad_objects.rectangle_cad_object import RectangleCadObject
from BelfryCAD.gui.viewmodels.cad_viewmodels.rectangle_viewmodel import RectangleViewModel
from BelfryCAD.gui.graphics_items.cad_polygon_graphics_item import CadPolygonGraphicsItem
from BelfryCAD.gui.widgets.cad_scene import CadScene
from BelfryCAD.cad_geometry import Point2D

class MockDocumentWindow:
    """Mock DocumentWindow for testing."""
    pass

def test_rectangle_viewmodel_uses_polygon_graphics():
    """Test that RectangleViewModel creates CadPolygonGraphicsItem."""
    print("Testing RectangleViewModel uses CadPolygonGraphicsItem...")
    
    # Create test objects
    document = Document()
    mock_window = MockDocumentWindow()
    
    # Create rectangle object
    rect_obj = RectangleCadObject(
        document=document,
        corner1=Point2D(10, 10),
        corner2=Point2D(60, 40),
        color="blue",
        line_width=2.0
    )
    
    # Create viewmodel
    viewmodel = RectangleViewModel(mock_window, rect_obj)
    
    # Create scene and update view
    scene = CadScene()
    viewmodel.update_view(scene)
    
    # Check that view items were created
    assert len(viewmodel._view_items) == 1
    view_item = viewmodel._view_items[0]
    
    # Verify it's a CadPolygonGraphicsItem, not CadRectangleGraphicsItem
    assert isinstance(view_item, CadPolygonGraphicsItem)
    print("   ✓ RectangleViewModel creates CadPolygonGraphicsItem")
    
    # Verify the polygon has 4 points (rectangle corners)
    # Access the internal points through the _points attribute
    points = view_item._points
    assert len(points) == 4
    print("   ✓ Polygon has correct number of corners (4)")
    
    # Verify corner order (counter-clockwise)
    expected_corners = [
        viewmodel.corner1,    # Bottom-left
        viewmodel.corner4,    # Bottom-right  
        viewmodel.corner3,    # Top-right
        viewmodel.corner2     # Top-left
    ]
    
    for i, expected_corner in enumerate(expected_corners):
        actual_corner = points[i]
        assert actual_corner == expected_corner
    print("   ✓ Polygon corners are in correct order (counter-clockwise)")
    
    # Verify the graphics item has proper styling
    pen = view_item.pen()
    assert pen.color().name() == "#0000ff"  # Blue color
    assert pen.widthF() == 2.0
    print("   ✓ Polygon has correct styling (color and line width)")
    
    return True

def main():
    """Main function to run the test."""
    # Try to get existing QApplication or create a new one
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    try:
        if test_rectangle_viewmodel_uses_polygon_graphics():
            print("\n✅ All tests passed!")
            print("RectangleViewModel correctly uses CadPolygonGraphicsItem")
            return 0
        else:
            print("\n❌ Tests failed!")
            return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 