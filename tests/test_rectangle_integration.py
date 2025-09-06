#!/usr/bin/env python3
"""
Integration test for Rectangle Tool with ViewModel system.

This script tests the integration between RectangleTool, RectangleCadObject,
and RectangleViewModel through the CadObjectFactory.
"""

import sys
import os

# Add the src directory to the path so we can import BelfryCAD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.models.document import Document
from BelfryCAD.tools.polygon import RectangleTool
from BelfryCAD.models.cad_objects.rectangle_cad_object import RectangleCadObject
from BelfryCAD.gui.viewmodels.cad_object_factory import CadObjectFactory
from BelfryCAD.gui.viewmodels.cad_viewmodels.rectangle_viewmodel import RectangleViewModel
from BelfryCAD.cad_geometry import Point2D

class MockDocumentWindow:
    """Mock document window for testing."""
    
    def __init__(self):
        self.scene = None
    
    def get_scene(self):
        return self.scene
    
    def get_dpcm(self):
        return 96.0  # Default DPI

class MockPreferences:
    """Mock preferences for testing."""
    
    def get(self, key, default=None):
        return {"default_color": "blue", "default_line_width": 1.0}.get(key, default)

def test_rectangle_integration():
    """Test the full integration of Rectangle components."""
    print("Testing Rectangle Integration...")
    
    # Create test objects
    document = Document()
    preferences = MockPreferences()
    document_window = MockDocumentWindow()
    
    # Test 1: Tool creates CAD object
    print("1. Testing tool creates RectangleCadObject...")
    tool = RectangleTool(document_window, document, preferences)
    tool.points = [Point2D(0, 0), Point2D(100, 50)]
    
    rectangle_object = tool.create_object()
    
    assert rectangle_object is not None
    assert isinstance(rectangle_object, RectangleCadObject)
    assert rectangle_object.width == 100
    assert rectangle_object.height == 50
    print("   ✓ Tool creates RectangleCadObject correctly")
    
    # Test 2: Factory creates ViewModel
    print("2. Testing factory creates RectangleViewModel...")
    factory = CadObjectFactory(document_window)
    
    viewmodel = factory.create_viewmodel(rectangle_object)
    
    assert viewmodel is not None
    assert isinstance(viewmodel, RectangleViewModel)
    assert viewmodel.object_type == "rectangle"
    print("   ✓ Factory creates RectangleViewModel correctly")
    
    # Test 3: ViewModel properties work
    print("3. Testing ViewModel properties...")
    from PySide6.QtCore import QPointF
    
    assert viewmodel.corner_point == QPointF(0, 0)
    assert viewmodel.width == 100
    assert viewmodel.height == 50
    assert viewmodel.center_point == QPointF(50, 25)
    assert viewmodel.opposite_corner == QPointF(100, 50)
    print("   ✓ ViewModel properties work correctly")
    
    # Test 4: ViewModel can modify object
    print("4. Testing ViewModel modifications...")
    # Test width modification
    original_width = viewmodel.width
    viewmodel.width = 120
    assert viewmodel.width == 120
    assert rectangle_object.width == 120  # Should update the underlying object
    
    # Test height modification
    viewmodel.height = 80
    assert viewmodel.height == 80
    assert rectangle_object.height == 80
    
    # Test corner modification
    viewmodel.corner_point = QPointF(10, 10)
    assert viewmodel.corner_point == QPointF(10, 10)
    assert rectangle_object.corner_point == Point2D(10, 10)
    print("   ✓ ViewModel modifications work correctly")
    
    # Test 5: Bounds calculation
    print("5. Testing bounds calculation...")
    bounds = viewmodel.get_bounds()
    expected_bounds = (10, 10, 130, 90)  # x1, y1, x2, y2
    assert bounds == expected_bounds
    print(f"   Bounds: {bounds}")
    print("   ✓ Bounds calculation works correctly")
    
    # Test 6: Point containment
    print("6. Testing point containment...")
    from PySide6.QtCore import QPointF
    
    # Point inside rectangle
    inside_point = QPointF(50, 50)
    assert viewmodel.contains_point(inside_point) == True
    
    # Point outside rectangle
    outside_point = QPointF(200, 200)
    assert viewmodel.contains_point(outside_point) == False
    print("   ✓ Point containment works correctly")
    
    print("\n✅ All integration tests passed!")
    return True

def main():
    """Main function to run the integration test."""
    try:
        if test_rectangle_integration():
            print("\n🎉 Rectangle integration is working correctly!")
            print("Tool → CadObject → ViewModel chain works properly.")
        else:
            print("\n❌ Rectangle integration tests failed!")
            return 1
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 