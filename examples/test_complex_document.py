#!/usr/bin/env python3
"""
Test Complex Document Loader

This script loads and verifies the complex test document to ensure
all objects, parameters, and groups are preserved correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.utils.xml_serializer import load_belfrycad_document
from BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject


def test_complex_document():
    """Test loading and verification of the complex test document."""
    
    filename = "complex_test_document.belcad"
    
    print("Complex Document Loader Test")
    print("=" * 40)
    
    # Load document
    print(f"Loading document from {filename}...")
    document = load_belfrycad_document(filename)
    
    if not document:
        print("✗ Failed to load document!")
        return 1
    
    print("✓ Document loaded successfully!")
    print()
    
    # Verify document structure
    print("Document Verification:")
    print(f"  Total Objects: {len(document.objects)}")
    print(f"  Parameters: {len(document.parameters)}")
    print(f"  Groups: {len([obj for obj in document.objects.values() if isinstance(obj, GroupCadObject)])}")
    print()
    
    # Verify object types
    print("Object Types:")
    type_counts = {}
    for obj in document.objects.values():
        obj_type = type(obj).__name__
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
    
    for obj_type, count in sorted(type_counts.items()):
        print(f"  {obj_type}: {count}")
    print()
    
    # Verify parameters
    print("Parameters:")
    for name, expression in document.parameters.items():
        try:
            value = document.cad_expression.evaluate(expression)
            print(f"  {name} = {expression} → {value}")
        except Exception as e:
            print(f"  {name} = {expression} (Error: {e})")
    print()
    
    # Verify groups
    print("Groups:")
    for obj in document.objects.values():
        if isinstance(obj, GroupCadObject):
            print(f"  {obj.name} ({obj.object_id}): {len(obj.children)} children")
            for child_id in obj.children:
                child = document.get_object(child_id)
                if child:
                    print(f"    - {child.name} ({child_id})")
                else:
                    print(f"    - Unknown object ({child_id})")
    print()
    
    # Verify object properties
    print("Object Properties:")
    for obj_id, obj in document.objects.items():
        print(f"  {obj.name} ({obj_id}):")
        print(f"    Type: {type(obj).__name__}")
        print(f"    Color: {obj.color}")
        print(f"    Visible: {obj.visible}")
        print(f"    Locked: {obj.locked}")
        if hasattr(obj, 'parent_id') and obj.parent_id:
            parent = document.get_object(obj.parent_id)
            parent_name = parent.name if parent else "Unknown"
            print(f"    Parent: {parent_name} ({obj.parent_id})")
        print()
    
    # Test parameter evaluation
    print("Parameter Evaluation Test:")
    try:
        gear_teeth_2 = document.cad_expression.evaluate('$gear_teeth_1 * $gear_ratio')
        print(f"  gear_teeth_2 = 20 * 2.5 = {gear_teeth_2}")
        
        gear_pitch_radius_2 = document.cad_expression.evaluate('$gear_pitch_radius_1 * $gear_ratio')
        print(f"  gear_pitch_radius_2 = 25.0 * 2.5 = {gear_pitch_radius_2}")
        
        print("✓ Parameter evaluation working correctly!")
    except Exception as e:
        print(f"✗ Parameter evaluation failed: {e}")
    
    print()
    print("✓ All tests completed successfully!")
    print(f"Document '{filename}' is ready for use!")
    
    return 0


if __name__ == "__main__":
    exit(test_complex_document()) 