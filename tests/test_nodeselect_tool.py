#!/usr/bin/env python3
"""
Test script for the NodeSelectTool implementation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtCore import QPointF

from src.tools.nodeselect import NodeSelectTool
from src.core.cad_objects import CADObject, ObjectType, Point
from src.core.document import Document


class MockPreferences:
    def get(self, key, default=None):
        return default


class MockDocument:
    def __init__(self):
        self.objects = MockObjectManager()
        self.modified = False
    
    def mark_modified(self):
        self.modified = True


class MockObjectManager:
    def __init__(self):
        self.test_objects = []
        # Create a test line object
        line_obj = CADObject(
            object_id=1,
            object_type=ObjectType.LINE,
            coords=[Point(10, 10), Point(50, 50)]
        )
        self.test_objects.append(line_obj)
        
        # Create a test bezier object  
        bezier_obj = CADObject(
            object_id=2,
            object_type=ObjectType.BEZIER,
            coords=[Point(100, 100), Point(120, 80), Point(140, 120), Point(160, 100)]
        )
        self.test_objects.append(bezier_obj)
    
    def get_all_objects(self):
        return self.test_objects
    
    def remove_object(self, obj_id):
        self.test_objects = [obj for obj in self.test_objects if obj.id != str(obj_id)]


def test_nodeselect_tool():
    """Test the NodeSelectTool functionality"""
    print("Testing NodeSelectTool...")
    
    app = QApplication([])
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    document = MockDocument()
    preferences = MockPreferences()
    
    # Create the tool
    tool = NodeSelectTool(scene, document, preferences)
    
    # Test tool definition
    definitions = tool._get_definition()
    assert len(definitions) == 1
    definition = definitions[0]
    
    print(f"✓ Tool token: {definition.token}")
    print(f"✓ Tool name: {definition.name}")
    print(f"✓ Tool icon: {definition.icon}")
    print(f"✓ Tool cursor: {definition.cursor}")
    
    assert definition.token == "NODESEL"
    assert definition.name == "Select Nodes"
    assert definition.icon == "tool-nodesel"
    assert definition.cursor == "top_left_arrow"
    
    # Test node finding
    print("\nTesting node detection...")
    
    # Should find node near line start point (10, 10)
    node_info = tool._find_node_near_point(12, 12, tolerance=5.0)
    assert node_info is not None
    obj_id, node_num = node_info
    print(f"✓ Found node: object {obj_id}, node {node_num}")
    
    # Should find node near bezier control point
    node_info = tool._find_node_near_point(122, 82, tolerance=5.0)
    assert node_info is not None
    obj_id, node_num = node_info
    print(f"✓ Found bezier node: object {obj_id}, node {node_num}")
    
    # Should not find node far away
    node_info = tool._find_node_near_point(500, 500, tolerance=5.0)
    assert node_info is None
    print("✓ Correctly rejected distant point")
    
    # Test node selection
    print("\nTesting node selection...")
    
    # Select first node of line
    tool._select_node("1", 1)
    assert tool._is_node_selected("1", 1)
    assert tool.get_selected_node_count() == 1
    print("✓ Node selection works")
    
    # Select second node of same object
    tool._select_node("1", 2)
    assert tool._is_node_selected("1", 2)
    assert tool.get_selected_node_count() == 2
    print("✓ Multiple node selection works")
    
    # Test deselection
    tool._deselect_node("1", 1)
    assert not tool._is_node_selected("1", 1)
    assert tool.get_selected_node_count() == 1
    print("✓ Node deselection works")
    
    # Test clear all
    tool.clear_all_selections()
    assert tool.get_selected_node_count() == 0
    assert tool.get_selected_object_count() == 0
    print("✓ Clear all selections works")
    
    # Test object selection
    print("\nTesting object selection...")
    line_obj = document.objects.get_all_objects()[0]
    tool._select_object(line_obj)
    assert tool.get_selected_object_count() == 1
    assert line_obj.selected
    print("✓ Object selection works")
    
    # Test object finding
    found_obj = tool._find_object_near_point(30, 30)  # Should be near the line
    assert found_obj is not None
    print(f"✓ Found object: {found_obj.object_type}")
    
    print("\nAll tests passed! ✓")
    
    # Show the view briefly to verify visual setup
    view.show()
    app.processEvents()
    
    return True


if __name__ == "__main__":
    success = test_nodeselect_tool()
    if success:
        print("\nNodeSelectTool implementation is working correctly!")
        sys.exit(0)
    else:
        print("\nTests failed!")
        sys.exit(1)
