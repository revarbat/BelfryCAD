#!/usr/bin/env python3
"""
Test script for the layers.py module to verify the translation is working correctly.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.layers import LayerManager, Layer


def test_layer_manager():
    """Test basic layer manager functionality."""
    print("Testing LayerManager...")
    
    # Create a layer manager
    lm = LayerManager("test_canvas")
    
    # Initialize layers
    lm.init_layers()
    
    # Test that we have one layer after initialization
    layer_ids = lm.get_layer_ids()
    print(f"Layer IDs after init: {layer_ids}")
    assert len(layer_ids) == 1, f"Expected 1 layer, got {len(layer_ids)}"
    
    # Test current layer
    current = lm.get_current_layer()
    print(f"Current layer: {current}")
    assert current == layer_ids[0], "Current layer should be the first created layer"
    
    # Test layer properties
    layer_name = lm.get_layer_name(current)
    print(f"Default layer name: {layer_name}")
    assert layer_name == "Layer 1", f"Expected 'Layer 1', got '{layer_name}'"
    
    # Test setting layer properties
    lm.set_layer_name(current, "Background")
    assert lm.get_layer_name(current) == "Background"
    
    lm.set_layer_color(current, "blue")
    assert lm.get_layer_color(current) == "blue"
    
    lm.set_layer_visible(current, False)
    assert not lm.is_layer_visible(current)
    
    lm.set_layer_locked(current, True)
    assert lm.is_layer_locked(current)
    
    print("✓ Basic layer properties work correctly")
    
    # Test creating additional layers
    layer2 = lm.create_layer("Foreground")
    layer3 = lm.create_layer()  # Should auto-name
    
    layer_ids = lm.get_layer_ids()
    print(f"Layer IDs after creating more: {layer_ids}")
    assert len(layer_ids) == 3, f"Expected 3 layers, got {len(layer_ids)}"
    
    assert lm.get_layer_name(layer2) == "Foreground"
    assert lm.get_layer_name(layer3) == "Layer 3"
    
    print("✓ Layer creation works correctly")
    
    # Test layer lookup by name
    found_id = lm.get_layer_by_name("Foreground")
    assert found_id == layer2, f"Expected {layer2}, got {found_id}"
    
    # Test object management
    lm.add_object_to_layer(layer2, 100)
    lm.add_object_to_layer(layer2, 101)
    lm.add_object_to_layer(layer2, 102)
    
    objects = lm.get_layer_objects(layer2)
    print(f"Objects in layer {layer2}: {objects}")
    assert objects == [100, 101, 102], f"Expected [100, 101, 102], got {objects}"
    
    # Test object removal
    lm.remove_object_from_layer(layer2, 101)
    objects = lm.get_layer_objects(layer2)
    assert objects == [100, 102], f"Expected [100, 102], got {objects}"
    
    print("✓ Object management works correctly")
    
    # Test layer reordering
    original_order = lm.get_layer_ids()
    print(f"Original order: {original_order}")
    
    # Move layer3 to position 0 (top)
    lm.reorder_layer(layer3, 0)
    new_order = lm.get_layer_ids()
    print(f"After reordering: {new_order}")
    assert new_order[0] == layer3, "Layer 3 should be at position 0"
    
    print("✓ Layer reordering works correctly")
    
    # Test serialization
    layer_data = lm.serialize_layer(layer2)
    print(f"Serialized layer data: {layer_data}")
    
    expected_keys = {"layerid", "pos", "name", "visible", "locked", "color", "cutbit", "cutdepth"}
    assert set(layer_data.keys()) == expected_keys, f"Missing serialization keys"
    
    print("✓ Layer serialization works correctly")
    
    # Test layer deletion
    lm.delete_layer(layer3)
    layer_ids = lm.get_layer_ids()
    print(f"Layer IDs after deletion: {layer_ids}")
    assert layer3 not in layer_ids, "Layer 3 should be deleted"
    assert len(layer_ids) == 2, f"Expected 2 layers, got {len(layer_ids)}"
    
    print("✓ Layer deletion works correctly")
    
    print("✅ All tests passed!")


if __name__ == "__main__":
    test_layer_manager()
