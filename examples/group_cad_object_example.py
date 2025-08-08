"""
Example demonstrating GroupCadObject functionality.

This example shows how to create groups, add objects to groups,
nest groups, and perform operations on groups.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.BelfryCAD.models.document import Document
from src.BelfryCAD.utils.geometry import Point2D


def main():
    """Demonstrate GroupCadObject functionality."""
    print("Creating a new CAD document...")
    doc = Document()
    
    # Create some basic shapes
    print("\nCreating basic shapes...")
    line1_id = doc.create_line(Point2D(0, 0), Point2D(10, 0))
    line2_id = doc.create_line(Point2D(10, 0), Point2D(10, 10))
    line3_id = doc.create_line(Point2D(10, 10), Point2D(0, 10))
    line4_id = doc.create_line(Point2D(0, 10), Point2D(0, 0))
    
    circle1_id = doc.create_circle(Point2D(5, 5), Point2D(7, 5))
    
    print(f"Created shapes: {[line1_id, line2_id, line3_id, line4_id, circle1_id]}")
    
    # Create a group for the rectangle
    print("\nCreating a group for the rectangle...")
    rectangle_group_id = doc.create_group("Rectangle")
    print(f"Created group: {rectangle_group_id}")
    
    # Add the rectangle lines to the group
    for line_id in [line1_id, line2_id, line3_id, line4_id]:
        success = doc.add_to_group(line_id, rectangle_group_id)
        print(f"Added {line_id} to group: {success}")
    
    # Create a nested group for the circle
    print("\nCreating a nested group for the circle...")
    circle_group_id = doc.create_group("Circle")
    print(f"Created circle group: {circle_group_id}")
    
    # Add circle to its group
    success = doc.add_to_group(circle1_id, circle_group_id)
    print(f"Added circle to group: {success}")
    
    # Add circle group to rectangle group (nesting)
    success = doc.add_to_group(circle_group_id, rectangle_group_id)
    print(f"Added circle group to rectangle group: {success}")
    
    # Display the hierarchy
    print("\nDocument hierarchy:")
    print(f"Root groups: {[g.name for g in doc.get_root_groups()]}")
    
    rectangle_group = doc.get_object(rectangle_group_id)
    print(f"Rectangle group children: {rectangle_group.children}")
    
    circle_group = doc.get_object(circle_group_id)
    print(f"Circle group children: {circle_group.children}")
    print(f"Circle group parent: {circle_group.parent_id}")
    
    # Test group bounds
    print(f"\nRectangle group bounds: {rectangle_group.get_bounds()}")
    print(f"Circle group bounds: {circle_group.get_bounds()}")
    
    # Test group transformation
    print("\nTranslating the rectangle group...")
    rectangle_group.translate(5, 5)
    
    # Check that all children were moved
    line1 = doc.get_object(line1_id)
    print(f"Line 1 start point after translation: {line1.start_point}")
    
    # Test removing from group
    print("\nRemoving circle from its group...")
    success = doc.remove_from_group(circle1_id)
    print(f"Removed circle from group: {success}")
    print(f"Circle parent after removal: {doc.get_object(circle1_id).parent_id}")
    
    # Test deleting a group with children
    print("\nDeleting the circle group...")
    success = doc.remove_object(circle_group_id)
    print(f"Deleted circle group: {success}")
    print(f"Circle still exists: {doc.get_object(circle1_id) is not None}")
    print(f"Circle parent after group deletion: {doc.get_object(circle1_id).parent_id}")
    
    print("\nExample completed successfully!")


if __name__ == "__main__":
    main() 