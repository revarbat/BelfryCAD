#!/usr/bin/env python3
"""
Example usage of BelfryCAD XML Serializer

This example demonstrates how to:
1. Create a document with various CAD objects
2. Add parameters and constraints
3. Save the document to a zip-compressed XML file
4. Load the document back from the file
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
from BelfryCAD.utils.xml_serializer import save_belfrycad_document, load_belfrycad_document
from BelfryCAD.cad_geometry import Point2D
from BelfryCAD.utils.cad_expression import CadExpression


def create_sample_document():
    """Create a sample document with various CAD objects."""
    print("Creating sample document...")
    
    # Create document
    document = Document()
    
    # Add parameters
    document.parameters = {
        'radius': '2.5',
        'height': '2 * $radius',
        'angle': '45º',
        'width': '10.0',
        'thickness': '0.5'
    }
    document.cad_expression = CadExpression(document.parameters)
    
    # Create a line
    line1 = LineCadObject(document, Point2D(0, 0), Point2D(10, 0), "black", 0.05)
    line1.name = "Base Line"
    document.objects[line1.object_id] = line1
    
    # Create a circle
    circle1 = CircleCadObject(document, Point2D(5, 5), Point2D(7.5, 5), "blue", 0.05)
    circle1.name = "Main Circle"
    document.objects[circle1.object_id] = circle1
    
    # Create an arc
    arc1 = ArcCadObject(document, Point2D(5, 5), Point2D(7.5, 5), Point2D(5, 7.5), "red", 0.05)
    arc1.name = "Top Arc"
    document.objects[arc1.object_id] = arc1
    
    # Create an ellipse
    ellipse1 = EllipseCadObject(document, Point2D(15, 5), Point2D(20, 5), Point2D(15, 7), "green", 0.05)
    ellipse1.name = "Main Ellipse"
    document.objects[ellipse1.object_id] = ellipse1
    
    # Create a bezier curve
    bezier_points = [
        Point2D(0, 10),
        Point2D(2, 13),
        Point2D(8, 13),
        Point2D(10, 10)
    ]
    bezier1 = CubicBezierCadObject(document, bezier_points, "purple", 0.05)
    bezier1.name = "Bezier Curve"
    document.objects[bezier1.object_id] = bezier1
    
    # Create a gear
    gear1 = GearCadObject(document, Point2D(20, 0), 3.0, 12, 20.0, "orange", 0.05)
    gear1.name = "Sample Gear"
    document.objects[gear1.object_id] = gear1
    
    # Create a group
    group1 = GroupCadObject(document, "Main Group", "black", None)
    document.objects[group1.object_id] = group1
    
    # Add some objects to the group
    line2 = LineCadObject(document, Point2D(0, 15), Point2D(5, 15), "red", 0.05)
    line2.name = "Line in Group"
    line2.parent_id = group1.object_id
    document.objects[line2.object_id] = line2
    group1.add_child(line2.object_id)
    
    circle2 = CircleCadObject(document, Point2D(2.5, 17.5), Point2D(3.5, 17.5), "blue", 0.05)
    circle2.name = "Circle in Group"
    circle2.parent_id = group1.object_id
    document.objects[circle2.object_id] = circle2
    group1.add_child(circle2.object_id)
    
    print(f"Created document with {len(document.objects)} objects")
    print(f"Parameters: {list(document.parameters.keys())}")
    
    return document


def print_document_info(document, title="Document"):
    """Print information about a document."""
    print(f"\n{title} Information:")
    print(f"  Objects: {len(document.objects)}")
    
    if hasattr(document, 'parameters') and document.parameters:
        print(f"  Parameters: {len(document.parameters)}")
        for name, expr in document.parameters.items():
            print(f"    {name} = {expr}")
    
    print("  Object types:")
    type_counts = {}
    for obj in document.objects.values():
        obj_type = type(obj).__name__
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
    
    for obj_type, count in type_counts.items():
        print(f"    {obj_type}: {count}")
    
    # Print groups and their children
    groups = [obj for obj in document.objects.values() if isinstance(obj, GroupCadObject)]
    if groups:
        print("  Groups:")
        for group in groups:
            print(f"    {group.name} ({group.object_id}): {len(group.children)} children")


def main():
    """Main example function."""
    print("BelfryCAD XML Serializer Example")
    print("=" * 40)
    
    # Create sample document
    original_doc = create_sample_document()
    print_document_info(original_doc, "Original")
    
    # Document preferences
    preferences = {
        'units': 'inches',
        'precision': 3,
        'use_fractions': False,
        'grid_visible': True,
        'show_rulers': True,
        'canvas_bg_color': '#ffffff',
        'grid_color': '#cccccc',
        'selection_color': '#0080ff'
    }
    
    # Save document
    filename = "sample_document.belcad"
    print(f"\nSaving document to {filename}...")
    
    if save_belfrycad_document(original_doc, filename, preferences):
        print("✓ Document saved successfully")
    else:
        print("✗ Failed to save document")
        return
    
    # Load document
    print(f"\nLoading document from {filename}...")
    loaded_doc = load_belfrycad_document(filename)
    
    if loaded_doc:
        print("✓ Document loaded successfully")
        print_document_info(loaded_doc, "Loaded")
        
        # Verify parameters were loaded correctly
        if hasattr(loaded_doc, 'parameters') and loaded_doc.parameters:
            print("\nParameter verification:")
            for name, expr in loaded_doc.parameters.items():
                try:
                    value = loaded_doc.cad_expression.evaluate(expr)
                    print(f"  {name} = {expr} → {value}")
                except Exception as e:
                    print(f"  {name} = {expr} → Error: {e}")
        
        # Verify objects were loaded correctly
        print("\nObject verification:")
        for obj_id, obj in loaded_doc.objects.items():
            print(f"  {obj.name} ({type(obj).__name__}) - ID: {obj_id}")
            if hasattr(obj, 'parent_id') and obj.parent_id:
                print(f"    Parent: {obj.parent_id}")
            if isinstance(obj, GroupCadObject):
                print(f"    Children: {obj.children}")
        
        # Check preferences
        if hasattr(loaded_doc, 'preferences') and loaded_doc.preferences:
            print("\nLoaded preferences:")
            for key, value in loaded_doc.preferences.items():
                print(f"  {key}: {value}")
        
    else:
        print("✗ Failed to load document")
    
    # Clean up
    if os.path.exists(filename):
        os.remove(filename)
        print(f"\nCleaned up: removed {filename}")


if __name__ == "__main__":
    main() 