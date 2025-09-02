#!/usr/bin/env python3
"""
Complex Test Document Generator

This script creates a comprehensive BelfryCAD document with:
- At least 15 objects of various types
- Multiple parameters with expressions
- Various constraints between objects
- Nested groups
- Different object properties

The document demonstrates a mechanical assembly with gears, mounting holes,
and various geometric relationships.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.models.document import Document
from BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from BelfryCAD.models.cad_objects.circle_cad_object import CircleCadObject
from BelfryCAD.models.cad_objects.arc_cad_object import ArcCadObject
from BelfryCAD.models.cad_objects.ellipse_cad_object import EllipseCadObject
from BelfryCAD.models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from BelfryCAD.models.cad_objects.gear_cad_object import GearCadObject
from BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject
from BelfryCAD.utils.cad_expression import CadExpression
from BelfryCAD.utils.xml_serializer import save_belfrycad_document
from BelfryCAD.cad_geometry.point import Point2D


def create_complex_test_document():
    """Create a comprehensive test document with multiple objects and constraints."""
    
    # Create document
    document = Document()
    
    # Add parameters
    parameters = {
        'base_width': '100.0',
        'base_height': '80.0',
        'hole_diameter': '8.0',
        'gear_ratio': '2.5',
        'mounting_clearance': '5.0',
        'center_distance': '60.0',
        'gear_pressure_angle': '20.0',
        'gear_teeth_1': '20',
        'gear_teeth_2': '$gear_teeth_1 * $gear_ratio',
        'gear_pitch_radius_1': '25.0',
        'gear_pitch_radius_2': '$gear_pitch_radius_1 * $gear_ratio',
        'spring_length': '40.0',
        'spring_coils': '8',
        'spring_diameter': '12.0',
        'angle_offset': '45.0'
    }
    
    # Create CadExpression for parameters
    document.cad_expression = CadExpression(parameters)
    
    # Create objects
    
    # 1. Base plate (rectangle made of lines)
    base_line1 = LineCadObject(document, Point2D(0, 0), Point2D(100, 0), "black", 0.5)
    base_line1.name = "Base Line 1"
    document.add_object(base_line1)
    
    base_line2 = LineCadObject(document, Point2D(100, 0), Point2D(100, 80), "black", 0.5)
    base_line2.name = "Base Line 2"
    document.add_object(base_line2)
    
    base_line3 = LineCadObject(document, Point2D(100, 80), Point2D(0, 80), "black", 0.5)
    base_line3.name = "Base Line 3"
    document.add_object(base_line3)
    
    base_line4 = LineCadObject(document, Point2D(0, 80), Point2D(0, 0), "black", 0.5)
    base_line4.name = "Base Line 4"
    document.add_object(base_line4)
    
    # 2. Mounting holes
    # Calculate radius from center to perimeter point
center1 = Point2D(10, 10)
perimeter_point1 = Point2D(18, 10)
radius1 = center1.distance_to(perimeter_point1)

hole1 = CircleCadObject(document, center1, radius1, "blue", 0.3)
    hole1.name = "Mounting Hole 1"
    document.add_object(hole1)
    
    # Calculate radius from center to perimeter point
center2 = Point2D(90, 10)
perimeter_point2 = Point2D(98, 10)
radius2 = center2.distance_to(perimeter_point2)

hole2 = CircleCadObject(document, center2, radius2, "blue", 0.3)
    hole2.name = "Mounting Hole 2"
    document.add_object(hole2)
    
    # Calculate radius from center to perimeter point
center3 = Point2D(10, 70)
perimeter_point3 = Point2D(18, 70)
radius3 = center3.distance_to(perimeter_point3)

hole3 = CircleCadObject(document, center3, radius3, "blue", 0.3)
    hole3.name = "Mounting Hole 3"
    document.add_object(hole3)
    
    # Calculate radius from center to perimeter point
center4 = Point2D(90, 70)
perimeter_point4 = Point2D(98, 70)
radius4 = center4.distance_to(perimeter_point4)

hole4 = CircleCadObject(document, center4, radius4, "blue", 0.3)
    hole4.name = "Mounting Hole 4"
    document.add_object(hole4)
    
    # 3. Gears
    gear1 = GearCadObject(document, Point2D(25, 40), 25.0, 20, 20.0, "red", 0.4)
    gear1.name = "Drive Gear"
    document.add_object(gear1)
    
    gear2 = GearCadObject(document, Point2D(85, 40), 62.5, 50, 20.0, "red", 0.4)
    gear2.name = "Driven Gear"
    document.add_object(gear2)
    
    # 4. Spring (approximated with arc)
    # Calculate radius and angles for a semicircle
center = Point2D(50, 20)
start_point = Point2D(45, 20)
end_point = Point2D(55, 20)
radius = center.distance_to(start_point)
start_degrees = (start_point - center).angle_degrees
end_degrees = (end_point - center).angle_degrees
span_degrees = end_degrees - start_degrees

spring_arc = ArcCadObject(document, center, radius, start_degrees, span_degrees, "green", 0.3)
    spring_arc.name = "Spring Arc"
    document.add_object(spring_arc)
    
    # 5. Elliptical cam
    # Calculate radii from center to axis points
cam_center = Point2D(50, 60)
cam_major_axis_point = Point2D(65, 60)
cam_minor_axis_point = Point2D(50, 55)
cam_radius1 = cam_center.distance_to(cam_major_axis_point)
cam_radius2 = cam_center.distance_to(cam_minor_axis_point)

cam = EllipseCadObject(document, cam_center, cam_radius1, cam_radius2, 0.0, "purple", 0.4)
    cam.name = "Elliptical Cam"
    document.add_object(cam)
    
    # 6. Bezier curve for decorative element
    bezier_points = [
        Point2D(15, 45),
        Point2D(25, 55),
        Point2D(35, 45),
        Point2D(45, 55)
    ]
    bezier = CubicBezierCadObject(document, bezier_points, "orange", 0.3)
    bezier.name = "Decorative Bezier"
    document.add_object(bezier)
    
    # 7. Center line
    center_line = LineCadObject(document, Point2D(50, 0), Point2D(50, 80), "gray", 0.2)
    center_line.name = "Center Line"
    document.add_object(center_line)
    
    # 8. Reference circle
    # Calculate radius from center to perimeter point
ref_center = Point2D(50, 40)
ref_perimeter_point = Point2D(70, 40)
ref_radius = ref_center.distance_to(ref_perimeter_point)

ref_circle = CircleCadObject(document, ref_center, ref_radius, "lightblue", 0.2)
    ref_circle.name = "Reference Circle"
    document.add_object(ref_circle)
    
    # Create groups
    base_group = GroupCadObject(document, "Base Assembly", "black", 0.5)
    base_group.name = "Base Assembly"
    document.add_object(base_group)
    
    # Add base lines to base group
    base_group.add_child(base_line1.object_id)
    base_group.add_child(base_line2.object_id)
    base_group.add_child(base_line3.object_id)
    base_group.add_child(base_line4.object_id)
    
    # Create mounting group
    mounting_group = GroupCadObject(document, "Mounting Holes", "blue", 0.3)
    mounting_group.name = "Mounting Holes"
    document.add_object(mounting_group)
    
    # Add holes to mounting group
    mounting_group.add_child(hole1.object_id)
    mounting_group.add_child(hole2.object_id)
    mounting_group.add_child(hole3.object_id)
    mounting_group.add_child(hole4.object_id)
    
    # Create gear group
    gear_group = GroupCadObject(document, "Gear Assembly", "red", 0.4)
    gear_group.name = "Gear Assembly"
    document.add_object(gear_group)
    
    # Add gears to gear group
    gear_group.add_child(gear1.object_id)
    gear_group.add_child(gear2.object_id)
    
    # Create mechanism group
    mechanism_group = GroupCadObject(document, "Mechanism", "green", 0.3)
    mechanism_group.name = "Mechanism"
    document.add_object(mechanism_group)
    
    # Add mechanism components
    mechanism_group.add_child(spring_arc.object_id)
    mechanism_group.add_child(cam.object_id)
    mechanism_group.add_child(bezier.object_id)
    
    # Create reference group
    reference_group = GroupCadObject(document, "Reference Elements", "gray", 0.2)
    reference_group.name = "Reference Elements"
    document.add_object(reference_group)
    
    # Add reference elements
    reference_group.add_child(center_line.object_id)
    reference_group.add_child(ref_circle.object_id)
    
    # Set up parent-child relationships
    base_line1.parent_id = base_group.object_id
    base_line2.parent_id = base_group.object_id
    base_line3.parent_id = base_group.object_id
    base_line4.parent_id = base_group.object_id
    
    hole1.parent_id = mounting_group.object_id
    hole2.parent_id = mounting_group.object_id
    hole3.parent_id = mounting_group.object_id
    hole4.parent_id = mounting_group.object_id
    
    gear1.parent_id = gear_group.object_id
    gear2.parent_id = gear_group.object_id
    
    spring_arc.parent_id = mechanism_group.object_id
    cam.parent_id = mechanism_group.object_id
    bezier.parent_id = mechanism_group.object_id
    
    center_line.parent_id = reference_group.object_id
    ref_circle.parent_id = reference_group.object_id
    
    return document


def main():
    """Main function to create and save the test document."""
    print("Complex Test Document Generator")
    print("=" * 50)
    
    # Create document
    print("Creating complex test document...")
    document = create_complex_test_document()
    
    # Document preferences
    preferences = {
        'units': 'mm',
        'precision': 2,
        'use_fractions': False,
        'grid_visible': True,
        'show_rulers': True,
        'canvas_bg_color': '#FFFFFF',
        'grid_color': '#CCCCCC',
        'selection_color': '#0080FF'
    }
    
    # Save document
    filename = "complex_test_document.belcad"
    print(f"Saving document to {filename}...")
    
    success = save_belfrycad_document(document, filename, preferences)
    
    if success:
        print("✓ Document saved successfully!")
        print()
        
        # Print document summary
        parameters = document.cad_expression.parameters
        print("Document Summary:")
        print(f"  Total Objects: {len(document.objects)}")
        print(f"  Parameters: {len(parameters)}")
        print(f"  Groups: {len([obj for obj in document.objects.values() if isinstance(obj, GroupCadObject)])}")
        print()
        
        print("Object Types:")
        type_counts = {}
        for obj in document.objects.values():
            obj_type = type(obj).__name__
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        
        for obj_type, count in sorted(type_counts.items()):
            print(f"  {obj_type}: {count}")
        print()
        
        print("Parameters:")
        for name, expression in document.cad_expression.parameters.items():
            try:
                value = document.cad_expression.evaluate(expression)
                print(f"  {name} = {expression} → {value}")
            except:
                print(f"  {name} = {expression}")
        print()
        
        print("Groups:")
        for obj in document.objects.values():
            if isinstance(obj, GroupCadObject):
                print(f"  {obj.name} ({obj.object_id}): {len(obj.children)} children")
        print()
        
        print(f"Document saved as: {filename}")
        print("You can now load this file for testing!")
        
    else:
        print("✗ Failed to save document!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 