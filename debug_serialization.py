#!/usr/bin/env python3
"""
Debug script to understand object serialization issue.
"""

import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.document import Document
from core.cad_objects import ObjectType, Point


def debug_object_serialization():
    """Debug object serialization to understand the structure."""
    print("Debugging object serialization...")
    
    # Create document with simple objects
    doc = Document()
    
    # Create a simple line
    line = doc.objects.create_object(
        ObjectType.LINE, 
        Point(0, 0), Point(10, 10),
        layer=1
    )
    
    # Create a circle
    circle = doc.objects.create_object(
        ObjectType.CIRCLE,
        Point(5, 5), Point(10, 5),
        layer=1
    )
    
    print(f"Created line with ID: {line.object_id}")
    print(f"Created circle with ID: {circle.object_id}")
    print(f"Total objects: {len(doc.objects.get_all_objects())}")
    
    # Check what gets serialized
    serialized = doc._serialize_native()
    
    print(f"\nSerialized object data:")
    objects_data = serialized.get("objects", [])
    for i, obj_data in enumerate(objects_data):
        print(f"Object {i}: {json.dumps(obj_data, indent=2, default=str)}")
    
    # Test deserialization
    print(f"\n--- Testing Deserialization ---")
    new_doc = Document()
    new_doc._deserialize_native(serialized)
    
    print(f"Objects after deserialization: {len(new_doc.objects.get_all_objects())}")
    for obj in new_doc.objects.get_all_objects():
        print(f"Restored object: {obj}")
    
    return len(new_doc.objects.get_all_objects()) == 2


if __name__ == "__main__":
    success = debug_object_serialization()
    print(f"\nDeserialization test: {'PASSED' if success else 'FAILED'}")
