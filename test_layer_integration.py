#!/usr/bin/env python3
"""
Integration test for the Layer system with Document class.
Tests that the translated layers.py works properly within the broader PyTkCAD system.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.document import Document
from core.layers import LayerManager
from core.cad_objects import ObjectType, Point


def test_document_layer_integration():
    """Test that Document class properly integrates with LayerManager."""
    print("Testing Document-Layer integration...")
    
    # Create a new document
    doc = Document()
    
    # Test that layer manager is initialized
    assert hasattr(doc, 'layers'), "Document should have layers attribute"
    assert isinstance(doc.layers, LayerManager), "Document.layers should be LayerManager"
    
    # Test that default layer is created
    layer_ids = doc.layers.get_layer_ids()
    print(f"Initial layer IDs: {layer_ids}")
    assert len(layer_ids) >= 1, "Should have at least one default layer"
    
    # Test current layer
    current = doc.layers.get_current_layer()
    print(f"Current layer: {current}")
    assert current in layer_ids, "Current layer should be in layer list"
    
    # Test layer creation through document
    layer2 = doc.layers.create_layer("Drawing Layer")
    layer3 = doc.layers.create_layer("Notes Layer") 
    
    layer_ids = doc.layers.get_layer_ids()
    print(f"Layer IDs after creation: {layer_ids}")
    assert len(layer_ids) == 3, f"Expected 3 layers, got {len(layer_ids)}"
    
    # Test setting layer properties
    doc.layers.set_layer_color(layer2, "red")
    doc.layers.set_layer_visible(layer3, False)
    
    assert doc.layers.get_layer_color(layer2) == "red"
    assert not doc.layers.is_layer_visible(layer3)
    
    print("✓ Basic document-layer integration works")
    
    # Test creating objects with layers
    # Create a line on layer2
    doc.layers.set_current_layer(layer2)
    line = doc.objects.create_object(
        ObjectType.LINE, 
        Point(0, 0), Point(10, 10),
        layer=layer2
    )
    
    # Add object to layer
    doc.layers.add_object_to_layer(layer2, line.object_id)
    
    # Verify object is in layer
    objects_in_layer = doc.layers.get_layer_objects(layer2)
    print(f"Objects in layer {layer2}: {objects_in_layer}")
    assert line.object_id in objects_in_layer, "Object should be in layer"
    
    print("✓ Object-layer association works")
    
    # Test document reset
    doc.new()
    
    # Verify layers are reset but still have default
    layer_ids = doc.layers.get_layer_ids()
    print(f"Layer IDs after document reset: {layer_ids}")
    assert len(layer_ids) >= 1, "Should have at least one layer after reset"
    
    # Verify objects are cleared
    all_objects = doc.objects.get_all_objects()
    assert len(all_objects) == 0, "All objects should be cleared after reset"
    
    print("✓ Document reset works correctly")
    
    print("✅ All Document-Layer integration tests passed!")


def test_document_serialization_with_layers():
    """Test that document serialization includes layer data."""
    print("\nTesting Document serialization with layers...")
    
    # Create document with layers and objects
    doc = Document()
    
    # Create some layers
    layer1 = doc.layers.get_current_layer()
    doc.layers.set_layer_name(layer1, "Base Layer")
    doc.layers.set_layer_color(layer1, "blue")
    
    layer2 = doc.layers.create_layer("Detail Layer")
    doc.layers.set_layer_color(layer2, "red")
    doc.layers.set_layer_visible(layer2, False)
    
    layer3 = doc.layers.create_layer("Notes")
    doc.layers.set_layer_locked(layer3, True)
    doc.layers.set_layer_cut_depth(layer3, 0.5)
    
    # Create some objects
    line1 = doc.objects.create_object(
        ObjectType.LINE, 
        Point(0, 0), Point(5, 5),
        layer=layer1
    )
    doc.layers.add_object_to_layer(layer1, line1.object_id)
    
    line2 = doc.objects.create_object(
        ObjectType.LINE,
        Point(10, 10), Point(15, 15), 
        layer=layer2
    )
    doc.layers.add_object_to_layer(layer2, line2.object_id)
    
    # Test serialization
    serialized = doc._serialize_native()
    print(f"Serialized keys: {list(serialized.keys())}")
    
    assert "layers" in serialized, "Serialization should include layers"
    assert "objects" in serialized, "Serialization should include objects"
    
    layers_data = serialized["layers"]
    print(f"Layer data keys: {list(layers_data.keys())}")
    
    assert "layer_data" in layers_data, "Should have layer_data"
    assert "current_layer" in layers_data, "Should have current_layer"
    assert "layer_order" in layers_data, "Should have layer_order"
    
    layer_data = layers_data["layer_data"]
    print(f"Serialized layer count: {len(layer_data)}")
    assert len(layer_data) == 3, f"Should serialize 3 layers, got {len(layer_data)}"
    
    # Verify layer properties are serialized
    for layer_id, layer_info in layer_data.items():
        print(f"Layer {layer_id}: {layer_info}")
        assert "name" in layer_info, f"Layer {layer_id} should have name"
        assert "color" in layer_info, f"Layer {layer_id} should have color"
        assert "visible" in layer_info, f"Layer {layer_id} should have visible"
        assert "locked" in layer_info, f"Layer {layer_id} should have locked"
    
    print("✓ Layer serialization works correctly")
    
    # Test deserialization
    doc2 = Document()
    doc2._deserialize_native(serialized)
    
    # Verify layers are restored
    restored_layer_ids = doc2.layers.get_layer_ids()
    print(f"Restored layer IDs: {restored_layer_ids}")
    assert len(restored_layer_ids) == 3, f"Should restore 3 layers, got {len(restored_layer_ids)}"
    
    # Verify layer properties
    for layer_id in restored_layer_ids:
        layer_info = doc2.layers.get_layer_info(layer_id)
        if layer_info:
            print(f"Restored layer {layer_id}: {layer_info.name}, color={layer_info.color}")
    
    # Find layers by name to verify properties
    base_layer_id = doc2.layers.get_layer_by_name("Base Layer")
    detail_layer_id = doc2.layers.get_layer_by_name("Detail Layer")
    notes_layer_id = doc2.layers.get_layer_by_name("Notes")
    
    assert base_layer_id is not None, "Base Layer should be restored"
    assert detail_layer_id is not None, "Detail Layer should be restored"
    assert notes_layer_id is not None, "Notes layer should be restored"
    
    assert doc2.layers.get_layer_color(base_layer_id) == "blue"
    assert doc2.layers.get_layer_color(detail_layer_id) == "red"
    assert not doc2.layers.is_layer_visible(detail_layer_id)
    assert doc2.layers.is_layer_locked(notes_layer_id)
    assert doc2.layers.get_layer_cut_depth(notes_layer_id) == 0.5
    
    print("✓ Layer deserialization works correctly")
    
    # Verify objects are restored
    restored_objects = doc2.objects.get_all_objects()
    print(f"Restored {len(restored_objects)} objects")
    assert len(restored_objects) == 2, f"Should restore 2 objects, got {len(restored_objects)}"
    
    print("✅ All serialization tests passed!")


if __name__ == "__main__":
    test_document_layer_integration()
    test_document_serialization_with_layers()
    print("\n🎉 All integration tests passed! Layer system is successfully integrated.")
