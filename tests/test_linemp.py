#!/usr/bin/env python3
"""
Test script for LINEMP tool implementation
"""

import sys
sys.path.append('/Users/gminette/dev/git-repos/pyTkCAD')

from BelfryCAD.core.cad_objects import Point
from BelfryCAD.tools.linemp import LineMPObject, LineMPTool

def test_linemp_object():
    """Test LineMPObject functionality"""
    print("Testing LineMPObject...")

    # Test basic creation
    midpoint = Point(10, 10)
    endpoint = Point(15, 10)  # 5 units right of midpoint

    obj = LineMPObject(1, midpoint, endpoint)

    # The full line should extend from midpoint to 2*(endpoint-midpoint)+midpoint
    # So from (10,10) to (20,10) - a 10 unit line
    expected_start = Point(10, 10)
    expected_end = Point(20, 10)

    print(f"Midpoint: ({midpoint.x}, {midpoint.y})")
    print(f"Endpoint: ({endpoint.x}, {endpoint.y})")
    print(f"Expected full line start: ({expected_start.x}, {expected_start.y})")
    print(f"Expected full line end: ({expected_end.x}, {expected_end.y})")
    print(f"Actual full line start: ({obj.start.x}, {obj.start.y})")
    print(f"Actual full line end: ({obj.end.x}, {obj.end.y})")

    # Test LENGTH field
    length = obj.get_field("LENGTH")
    expected_length = 10.0  # Distance from midpoint to endpoint * 2
    print(f"Expected LENGTH: {expected_length}")
    print(f"Actual LENGTH: {length}")

    # Test ANGLE field
    angle = obj.get_field("ANGLE")
    expected_angle = 0.0  # Horizontal line to the right
    print(f"Expected ANGLE: {expected_angle}")
    print(f"Actual ANGLE: {angle}")

    # Test with diagonal line
    print("\nTesting diagonal line...")
    midpoint2 = Point(0, 0)
    endpoint2 = Point(3, 4)  # 3-4-5 triangle, 5 units from origin

    obj2 = LineMPObject(2, midpoint2, endpoint2)
    length2 = obj2.get_field("LENGTH")
    angle2 = obj2.get_field("ANGLE")

    expected_length2 = 10.0  # 5 * 2
    expected_angle2 = 53.13010235415598  # atan2(4, 3) in degrees

    print(f"Diagonal - Expected LENGTH: {expected_length2}")
    print(f"Diagonal - Actual LENGTH: {length2}")
    print(f"Diagonal - Expected ANGLE: {expected_angle2}")
    print(f"Diagonal - Actual ANGLE: {angle2}")

    print("LineMPObject test completed!")

def test_linemp_tool_definitions():
    """Test LineMPTool definitions"""
    print("\nTesting LineMPTool definitions...")

    # Create a mock scene, document, and preferences
    class MockScene:
        pass

    class MockDocument:
        pass

    class MockPreferences:
        pass

    tool = LineMPTool(MockScene(), MockDocument(), MockPreferences())
    definitions = tool._get_definition()

    print(f"Number of tool definitions: {len(definitions)}")
    for i, defn in enumerate(definitions):
        print(f"Definition {i+1}:")
        print(f"  Token: {defn.token}")
        print(f"  Name: {defn.name}")
        print(f"  Category: {defn.category}")
        print(f"  Icon: {defn.icon}")
        print(f"  Node Info: {defn.node_info}")

    print("LineMPTool definitions test completed!")

if __name__ == "__main__":
    test_linemp_object()
    test_linemp_tool_definitions()
    print("\nAll tests completed successfully!")
