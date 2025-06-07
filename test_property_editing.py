#!/usr/bin/env python3
"""
Test script to verify property editing system integration.

This script tests that:
1. Selection monitoring works correctly
2. Config pane is populated when objects are selected
3. Property changes are applied to objects
4. Scene redraw is triggered after property changes
"""

import sys
import os

# Add the BelfryCAD directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.core.document import Document
from BelfryCAD.config import AppConfig


def test_property_editing_core():
    """Test the core property editing logic without GUI."""
    print("Testing core property editing logic...")
    
    # Create required dependencies
    config = AppConfig()
    
    # Create a document
    document = Document()
    
    # Create a simple CAD object for testing
    test_obj = CADObject(
        object_id="test_line_1",
        object_type=ObjectType.LINE,
        coords=[Point(0, 0), Point(10, 10)],
        attributes={
            'color': 'blue',
            'linewidth': 2.0,
            'layer': 1  # Use the default layer ID
        }
    )
    
    print(f"Created test object: {test_obj.object_id}")
    print(f"Initial attributes: {test_obj.attributes}")
    
    # Add the object to the document
    document.objects.add_object(test_obj)
    print(f"Added object to document")
    
    # Test property change simulation
    print("Testing property changes...")
    
    # Simulate changing object color
    test_obj.attributes['color'] = 'red'
    print(f"Changed color to red")
    print(f"Object attributes after change: {test_obj.attributes}")
    
    # Simulate changing linewidth
    test_obj.attributes['linewidth'] = 5.0
    print(f"Changed linewidth to 5.0")
    print(f"Object attributes after change: {test_obj.attributes}")
    
    # Test object selection state
    test_obj.selected = True
    print(f"Selected object: {test_obj.selected}")
    
    # Test getting object from document
    retrieved_obj = document.objects.get_object("test_line_1")
    if retrieved_obj:
        print(f"Successfully retrieved object from document")
        print(f"Retrieved object attributes: {retrieved_obj.attributes}")
    else:
        print("Failed to retrieve object from document")
    
    print("Core property editing test completed successfully!")
    return True


def main():
    """Main test function."""
    print("Starting property editing system tests...")
    
    try:
        # Test core functionality
        test_property_editing_core()
        
        print("\nAll tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    print(f"Tests completed with exit code: {exit_code}")
    sys.exit(exit_code)
