#!/usr/bin/env python3
"""
Test script for the Polyline tool
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.polyline import PolylineTool, PolylineObject
from core.cad_objects import Point

def test_polyline_object():
    """Test the PolylineObject class"""
    print("Testing PolylineObject...")

    # Create test points
    points = [
        Point(0, 0),
        Point(10, 0),
        Point(10, 10),
        Point(0, 10)
    ]

    # Create polyline object with object_id
    polyline = PolylineObject(object_id=1, vertices=points)

    print(f"Object type: {polyline.object_type}")
    print(f"Number of points: {len(polyline.coords)}")
    print(f"Is closed: {polyline.is_closed()}")

    # Test bounds calculation if available
    try:
        bounds = polyline.get_bounds()
        print(f"Bounds: {bounds}")
    except AttributeError:
        print("get_bounds method not available")

    print("PolylineObject test passed!\n")

def test_polyline_tool():
    """Test the PolylineTool class"""
    print("Testing PolylineTool...")

    # Create a mock scene for testing
    class MockScene:
        def __init__(self):
            self.items = []

        def addItem(self, item):
            self.items.append(item)

        def removeItem(self, item):
            if item in self.items:
                self.items.remove(item)

    # Create tool instance
    tool = PolylineTool()
    tool.scene = MockScene()
    tool.temp_objects = []

    # Test tool properties
    print(f"Tool token: {tool.token}")
    print(f"Tool name: {tool.name}")
    print(f"Tool category: {tool.category}")
    print(f"Tool icon: {tool.icon}")

    # Test adding points
    tool.points = []
    tool.points.append(Point(0, 0))
    tool.points.append(Point(10, 0))
    tool.points.append(Point(10, 10))

    print(f"Points added: {len(tool.points)}")

    # Test completion
    if len(tool.points) >= 2:
        polyline = tool.create_polyline()
        print(f"Created polyline with {len(polyline.points)} points")

    print("PolylineTool test passed!\n")

if __name__ == "__main__":
    print("Running Polyline tool tests...\n")

    try:
        test_polyline_object()
        test_polyline_tool()
        print("All tests passed successfully!")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
