#!/usr/bin/env python3
"""
Test script for Rectangle Tool functionality.

This script tests the Rectangle CAD tool to ensure it properly creates
RectangleCadObjects.
"""

import sys
import os

# Add the src directory to the path so we can import BelfryCAD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.models.document import Document
from BelfryCAD.tools.polygon import RectangleTool
from BelfryCAD.models.cad_objects.rectangle_cad_object import RectangleCadObject
from BelfryCAD.cad_geometry import Point2D

class MockDocumentWindow:
    """Mock document window for testing."""
    
    def __init__(self):
        self.scene = None
    
    def get_scene(self):
        return self.scene
    
    def get_dpcm(self):
        return 96.0  # Default DPI

def test_rectangle_tool():
    """Test the RectangleTool functionality."""
    print("Testing Rectangle Tool...")
    
    # Create test objects
    document = Document()
    # Create a simple mock preferences object
    class MockPreferences:
        def get(self, key, default=None):
            return {"default_color": "black", "default_line_width": 0.05}.get(key, default)
    
    preferences = MockPreferences()
    document_window = MockDocumentWindow()
    
    # Create the RectangleTool
    tool = RectangleTool(document_window, document, preferences)
    
    # Test 1: Check tool definition
    print("1. Testing tool definition...")
    assert len(tool.tool_definitions) == 1
    definition = tool.tool_definitions[0]
    assert definition.token == "RECTANGLE"
    assert definition.name == "Rectangle"
    assert definition.secondary_key == "R"
    assert definition.is_creator == True
    print("   ✓ Tool definition is correct")
    
    # Test 2: Test object creation with points
    print("2. Testing object creation...")
    # Simulate two points for rectangle corners
    tool.points = [Point2D(10, 10), Point2D(50, 40)]
    
    # Create the object
    cad_object = tool.create_object()
    
    # Verify the object
    assert cad_object is not None
    assert isinstance(cad_object, RectangleCadObject)
    assert cad_object.corner_point == Point2D(10, 10)  # Bottom-left corner
    assert cad_object.width == 40
    assert cad_object.height == 30
    assert cad_object.center_point == Point2D(30, 25)
    assert cad_object.opposite_corner == Point2D(50, 40)  # Top-right corner
    print("   ✓ Object creation works correctly")
    print(f"   Rectangle: {cad_object.corner_point} to {cad_object.opposite_corner}")
    print(f"   Dimensions: {cad_object.width} x {cad_object.height}")
    
    # Test 3: Test with reversed points (ensuring proper corner calculation)
    print("3. Testing with reversed points...")
    tool.points = [Point2D(50, 40), Point2D(10, 10)]  # Reversed order
    
    cad_object2 = tool.create_object()
    
    # Should still produce the same rectangle
    assert cad_object2.corner_point == Point2D(10, 10)  # Bottom-left corner
    assert cad_object2.width == 40
    assert cad_object2.height == 30
    print("   ✓ Reversed points handled correctly")
    
    # Test 4: Test with negative coordinates
    print("4. Testing with negative coordinates...")
    tool.points = [Point2D(-20, -10), Point2D(10, 20)]
    
    cad_object3 = tool.create_object()
    
    assert cad_object3.corner_point == Point2D(-20, -10)  # Bottom-left corner
    assert cad_object3.width == 30
    assert cad_object3.height == 30
    print("   ✓ Negative coordinates handled correctly")
    
    # Test 5: Test invalid input (wrong number of points)
    print("5. Testing invalid input...")
    tool.points = [Point2D(0, 0)]  # Only one point
    
    cad_object4 = tool.create_object()
    assert cad_object4 is None  # Should return None for invalid input
    print("   ✓ Invalid input handled correctly")
    
    # Test 6: Test color and line width from preferences
    print("6. Testing preferences...")
    # Create a preferences mock that returns specific values
    class MockPreferencesWithValues:
        def get(self, key, default=None):
            values = {"default_color": "red", "default_line_width": 2.0}
            return values.get(key, default)
    
    tool.preferences = MockPreferencesWithValues()
    tool.points = [Point2D(0, 0), Point2D(10, 10)]
    cad_object5 = tool.create_object()
    
    assert cad_object5.color == "red"
    assert cad_object5.line_width == 2.0
    print("   ✓ Preferences applied correctly")
    
    print("\n✅ All Rectangle Tool tests passed!")
    return True

def main():
    """Main function to run the test."""
    try:
        if test_rectangle_tool():
            print("\n🎉 Rectangle Tool is working correctly!")
            print("The tool properly creates RectangleCadObjects from user input.")
        else:
            print("\n❌ Rectangle Tool tests failed!")
            return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 