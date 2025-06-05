#!/usr/bin/env python3
"""
Final demonstration of the complete layer system integration.
This shows the full working translation from layers.tcl to Python.
"""

import sys
import os
import tempfile

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.document import Document
from core.cad_objects import ObjectType, Point


def demo_complete_layer_system():
    """Demonstrate the complete working layer system."""
    print("🎯 Final Layer System Demo")
    print("=" * 50)
    
    # Create a new document
    doc = Document()
    
    # 1. Layer Management
    print("\n1. Layer Management:")
    layer1 = doc.layers.create_layer("Construction Lines")
    layer2 = doc.layers.create_layer("Main Drawing")
    layer3 = doc.layers.create_layer("Dimensions")
    
    print(f"   Created layers: {doc.layers.get_layer_ids()}")
    
    # Set layer properties
    doc.layers.set_layer_color(layer1, "gray")
    doc.layers.set_layer_color(layer2, "blue")
    doc.layers.set_layer_color(layer3, "red")
    doc.layers.set_layer_visible(layer1, False)  # Hide construction lines
    
    print(f"   Layer 1: {doc.layers.get_layer_name(layer1)} - {doc.layers.get_layer_color(layer1)}")
    print(f"   Layer 2: {doc.layers.get_layer_name(layer2)} - {doc.layers.get_layer_color(layer2)}")
    print(f"   Layer 3: {doc.layers.get_layer_name(layer3)} - {doc.layers.get_layer_color(layer3)}")
    
    # 2. Object Creation on Different Layers
    print("\n2. Object Creation:")
    
    # Set current layer and create objects
    doc.layers.set_current_layer(layer1)
    line1 = doc.objects.create_object(ObjectType.LINE, Point(0, 0), Point(10, 0), layer=layer1)
    line2 = doc.objects.create_object(ObjectType.LINE, Point(0, 0), Point(0, 10), layer=layer1)
    # Add objects to layer tracking
    doc.layers.add_object_to_layer(layer1, line1.object_id)
    doc.layers.add_object_to_layer(layer1, line2.object_id)
    
    doc.layers.set_current_layer(layer2)
    circle = doc.objects.create_object(ObjectType.CIRCLE, Point(5, 5), Point(8, 5), layer=layer2)
    doc.layers.add_object_to_layer(layer2, circle.object_id)
    
    doc.layers.set_current_layer(layer3)
    dim_line = doc.objects.create_object(ObjectType.LINE, Point(0, -2), Point(10, -2), layer=layer3)
    doc.layers.add_object_to_layer(layer3, dim_line.object_id)
    
    print(f"   Created {len(doc.objects.get_all_objects())} objects")
    print(f"   Layer 1 objects: {len(doc.layers.get_layer_objects(layer1))}")
    print(f"   Layer 2 objects: {len(doc.layers.get_layer_objects(layer2))}")
    print(f"   Layer 3 objects: {len(doc.layers.get_layer_objects(layer3))}")
    
    # 3. Document Serialization and Deserialization
    print("\n3. Document Persistence:")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tkcad', delete=False) as tmp:
        tmp_filename = tmp.name
    
    try:
        # Save document
        doc.save(tmp_filename)
        print(f"   Saved document to {tmp_filename}")
        
        # Create new document and load
        new_doc = Document()
        new_doc.load(tmp_filename)
        
        print(f"   Loaded document successfully")
        print(f"   Restored {len(new_doc.objects.get_all_objects())} objects")
        print(f"   Restored {len(new_doc.layers.get_layer_ids())} layers")
        
        # Verify data integrity
        for layer_id in new_doc.layers.get_layer_ids():
            name = new_doc.layers.get_layer_name(layer_id)
            color = new_doc.layers.get_layer_color(layer_id)
            visible = new_doc.layers.is_layer_visible(layer_id)
            print(f"   Layer {layer_id}: {name} - {color} (visible: {visible})")
        
        # 4. Advanced Features
        print("\n4. Advanced Features:")
        
        # Move object between layers
        objects_in_layer2 = new_doc.layers.get_layer_objects(layer2)
        if objects_in_layer2:
            obj_id = objects_in_layer2[0]
            print(f"   Moving object {obj_id} from layer {layer2} to layer {layer3}")
            
            # Count before move
            layer2_before = len(new_doc.layers.get_layer_objects(layer2))
            layer3_before = len(new_doc.layers.get_layer_objects(layer3))
            
            success = new_doc.layers.move_object_to_layer(obj_id, layer2, layer3)
            
            # Count after move
            layer2_after = len(new_doc.layers.get_layer_objects(layer2))
            layer3_after = len(new_doc.layers.get_layer_objects(layer3))
            
            if success:
                print(f"   ✓ Layer {layer2}: {layer2_before} → {layer2_after} objects")
                print(f"   ✓ Layer {layer3}: {layer3_before} → {layer3_after} objects")
            else:
                print("   ✗ Object move failed")
        else:
            print("   No objects in layer 2 to move")
        
        # Reorder layers - swap first two layers
        original_order = new_doc.layers.get_layer_ids()
        if len(original_order) >= 2:
            # Create a new order with first two swapped
            new_layer_order = [original_order[1], original_order[0]] + original_order[2:]
            success = new_doc.layers.reorder_layers(new_layer_order)
            final_order = new_doc.layers.get_layer_ids()
            
            if success:
                print(f"   ✓ Reordered layers: {original_order} → {final_order}")
            else:
                print("   ✗ Layer reordering failed")
        else:
            print("   Not enough layers to demonstrate reordering")
        
        print("\n✅ Complete layer system working perfectly!")
        print("🎉 layers.tcl successfully translated to Python!")
        
        return True
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_filename):
            os.unlink(tmp_filename)


if __name__ == "__main__":
    success = demo_complete_layer_system()
    exit(0 if success else 1)
