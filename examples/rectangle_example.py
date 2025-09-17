#!/usr/bin/env python3
"""
Rectangle CAD Object Example

This example demonstrates the usage of RectangleCadObject.
"""

import sys
import os

# Add the src directory to the path so we can import BelfryCAD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.models.document import Document
from BelfryCAD.models.cad_objects.rectangle_cad_object import RectangleCadObject
from BelfryCAD.cad_geometry import Point2D

def main():
    """Main function to demonstrate rectangle usage."""
    print("Rectangle CAD Object Example")
    print("=" * 40)
    
    # Create a document
    document = Document()
    rectangles = []
    
    # Rectangle 1: Basic rectangle
    rect1 = RectangleCadObject(
        document=document,
        corner1=Point2D(0, 0),
        corner2=Point2D(50, 30),
        color="blue",
        line_width=1.0
    )
    rectangles.append(rect1)
    print(f"Rectangle 1: {rect1.corner1} to {rect1.corner3}")
    print(f"  Center: {rect1.center_point}")
    print(f"  Dimensions: {rect1.width} x {rect1.height}")
    print(f"  Bounds: {rect1.get_bounds()}")

    rect2 = RectangleCadObject(
        document=document,
        corner1=Point2D(60, 10),
        corner2=Point2D(100, 50),
        color="red",
        line_width=2.0
    )
    rectangles.append(rect2)
    print(f"\nRectangle 2 (Square): {rect2.corner1} to {rect2.corner3}")
    print(f"  Center: {rect2.center_point}")
    print(f"  Dimensions: {rect2.width} x {rect2.height}")

    # Rectangle 3: Tall rectangle 
    rect3 = RectangleCadObject(
        document=document,
        corner1=Point2D(130, 0),
        corner2=Point2D(150, 80),
        color="green",
        line_width=1.5
    )
    rectangles.append(rect3)
    print(f"\nRectangle 3 (Tall): {rect3.corner1} to {rect3.corner3}")
    print(f"  Center: {rect3.center_point}")
    print(f"  Dimensions: {rect3.width} x {rect3.height}")

    # --- Modifying Rectangle 1 ---
    print(f"\n--- Modifying Rectangle 1 ---")
    print(f"Original width: {rect1.width}")
    rect1.width = 75
    print(f"New width: {rect1.width}")
    print(f"New bounds: {rect1.get_bounds()}")

    # --- Moving Rectangle 2 ---
    print(f"\n--- Moving Rectangle 2 ---")
    print(f"Original corner: {rect2.corner1}")
    rect2.translate(10, -5)
    print(f"New corner after translate(10, -5): {rect2.corner1}")

    # --- Serialization Test ---
    print(f"\n--- Serialization Test ---")
    obj_data = rect1.get_object_data()
    print(f"Serialized data: {obj_data}")
    
    restored_rect = RectangleCadObject.create_object_from_data(
        document, "rectangle", obj_data
    )
    print(f"Restored rectangle bounds: {restored_rect.get_bounds()}")
    print(f"Original and restored are equal: {rect1.corner1 == restored_rect.corner1 and rect1.width == restored_rect.width and rect1.height == restored_rect.height}")
    
    # Demonstrate contains_point
    print(f"\n--- Point Containment Test ---")
    test_point = Point2D(25, 15)  # Should be inside Rectangle 1
    print(f"Point {test_point} is inside Rectangle 1: {rect1.contains_point(test_point)}")
    
    test_point2 = Point2D(200, 200)  # Should be outside
    print(f"Point {test_point2} is inside Rectangle 1: {rect1.contains_point(test_point2)}")

    # --- Summary ---
    print(f"\n--- Summary ---")
    print(f"Created {len(rectangles)} rectangles")
    print(f"  Rectangle 1: {rect1.width}x{rect1.height} at {rect1.corner1}")
    print(f"  Rectangle 2: {rect2.width}x{rect2.height} at {rect2.corner1}")
    print(f"  Rectangle 3: {rect3.width}x{rect3.height} at {rect3.corner1}")
    
    print("\n✅ Rectangle example completed successfully!")

if __name__ == "__main__":
    main() 