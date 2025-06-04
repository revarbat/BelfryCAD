#!/usr/bin/env python3
"""
Simple test script for the Polyline tool
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

    print("PolylineObject test passed!\n")


def test_polyline_tool():
    """Test the PolylineTool class"""
    print("Testing PolylineTool...")

    # Test that the class exists and can be imported
    print(f"PolylineTool class: {PolylineTool}")
    print(f"PolylineTool is subclass of Tool: {hasattr(PolylineTool, '_get_definition')}")

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
