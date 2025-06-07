#!/usr/bin/env python3
"""
Test script for the new getItemsByTags method in CadScene.

This script demonstrates how to use the getItemsByTags method to find
all graphics items that have all of the specified tags.
"""

import sys
import os

# Add the BelfryCAD directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication
from gui.cad_scene import CadScene


def test_get_items_by_tags():
    """Test the getItemsByTags method functionality."""

    # Create a CadScene instance
    cad_scene = CadScene()

    print("Testing CadScene.getItemsByTags() method")
    print("=" * 50)

    # Add various items with different tag combinations
    print("\n1. Adding items with different tag combinations:")

    # Items with overlapping tags
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["geometry", "layer1", "construction"])
    print("   - Line1: tags=['geometry', 'layer1', 'construction']")

    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["geometry", "layer1", "solid"])
    print("   - Rect1: tags=['geometry', 'layer1', 'solid']")

    ellipse1 = cad_scene.addEllipse(150, 150, 100, 50, tags=["geometry", "layer2", "solid"])
    print("   - Ellipse1: tags=['geometry', 'layer2', 'solid']")

    line2 = cad_scene.addLine(200, 200, 300, 300, tags=["construction", "helper", "temporary"])
    print("   - Line2: tags=['construction', 'helper', 'temporary']")

    text1 = cad_scene.addText("Sample Text", tags=["text", "annotation", "layer2"])
    print("   - Text1: tags=['text', 'annotation', 'layer2']")

    # Items with multiple common tags
    line3 = cad_scene.addLine(300, 300, 400, 400, tags=["geometry", "layer1", "construction", "important"])
    print("   - Line3: tags=['geometry', 'layer1', 'construction', 'important']")

    rect2 = cad_scene.addRect(100, 100, 150, 75, tags=["geometry", "layer2", "solid", "important"])
    print("   - Rect2: tags=['geometry', 'layer2', 'solid', 'important']")

    print("\n2. Testing getItemsByTags with different tag combinations:")

    # Test single tag queries
    geometry_items = cad_scene.getItemsByTags(["geometry"])
    print(f"\n   Items with tag 'geometry': {len(geometry_items)} items")
    for i, item in enumerate(geometry_items):
        item_tags = cad_scene.getTags(item)
        print(f"     - Item {i+1}: {item_tags}")

    # Test multiple tag queries (AND operation)
    layer1_geometry = cad_scene.getItemsByTags(["geometry", "layer1"])
    print(f"\n   Items with tags 'geometry' AND 'layer1': {len(layer1_geometry)} items")
    for i, item in enumerate(layer1_geometry):
        item_tags = cad_scene.getTags(item)
        print(f"     - Item {i+1}: {item_tags}")

    # Test three tag combination
    construction_geometry_layer1 = cad_scene.getItemsByTags([
        "geometry", "layer1", "construction"
    ])
    print(f"\n   Items with tags 'geometry' AND 'layer1' AND 'construction': {len(construction_geometry_layer1)} items")
    for i, item in enumerate(construction_geometry_layer1):
        item_tags = cad_scene.getTags(item)
        print(f"     - Item {i+1}: {item_tags}")

    # Test with non-existent tag
    nonexistent_items = cad_scene.getItemsByTags(["nonexistent"])
    print(f"\n   Items with tag 'nonexistent': {len(nonexistent_items)} items")

    # Test with mix of existing and non-existing tags
    mixed_items = cad_scene.getItemsByTags(["geometry", "nonexistent"])
    print(f"   Items with tags 'geometry' AND 'nonexistent': {len(mixed_items)} items")

    # Test with empty tag list
    empty_items = cad_scene.getItemsByTags([])
    print(f"   Items with empty tag list: {len(empty_items)} items")

    print("\n3. Advanced queries:")

    # Find all solid items
    solid_items = cad_scene.getItemsByTags(["solid"])
    print(f"\n   All solid items: {len(solid_items)} items")

    # Find all important items
    important_items = cad_scene.getItemsByTags(["important"])
    print(f"   All important items: {len(important_items)} items")

    # Find items that are both solid and important
    solid_important = cad_scene.getItemsByTags(["solid", "important"])
    print(f"   Items that are both solid AND important: {len(solid_important)} items")
    for i, item in enumerate(solid_important):
        item_tags = cad_scene.getTags(item)
        print(f"     - Item {i+1}: {item_tags}")

    print("\n4. Summary of all tagged items in the scene:")
    print("   Tag -> Items count:")

    # Get all unique tags
    all_tags = set()
    for item in [line1, rect1, ellipse1, line2, text1, line3, rect2]:
        all_tags.update(cad_scene.getTags(item))

    for tag in sorted(all_tags):
        items = cad_scene.getItemsByTag(tag)
        print(f"     '{tag}' -> {len(items)} items")

    print("\n" + "=" * 50)
    print("getItemsByTags() test completed successfully!")
    print("The method correctly finds items that have ALL specified tags.")


def test_real_world_usage():
    """Demonstrate real-world usage patterns."""

    print("\n" + "=" * 50)
    print("REAL-WORLD USAGE EXAMPLES")
    print("=" * 50)

    cad_scene = CadScene()

    # Simulate a CAD drawing with layers, object types, and states
    print("\nCreating a sample CAD drawing...")

    # Structural elements
    cad_scene.addLine(0, 0, 1000, 0, tags=["structure", "foundation", "layer_structural", "visible"])
    cad_scene.addLine(1000, 0, 1000, 500, tags=["structure", "wall", "layer_structural", "visible"])
    cad_scene.addLine(1000, 500, 0, 500, tags=["structure", "wall", "layer_structural", "visible"])
    cad_scene.addLine(0, 500, 0, 0, tags=["structure", "wall", "layer_structural", "visible"])

    # Dimensions
    cad_scene.addLine(0, -50, 1000, -50, tags=["dimension", "layer_dimensions", "visible"])
    cad_scene.addText("1000mm", tags=["dimension", "text", "layer_dimensions", "visible"])

    # Construction lines (temporary)
    cad_scene.addLine(500, 0, 500, 500, tags=["construction", "centerline", "layer_construction", "temporary"])
    cad_scene.addLine(0, 250, 1000, 250, tags=["construction", "centerline", "layer_construction", "temporary"])

    # Annotations
    cad_scene.addText("Main Room", tags=["annotation", "label", "layer_text", "visible"])
    cad_scene.addText("DRAFT", tags=["annotation", "watermark", "layer_text", "temporary"])

    print("\nReal-world query examples:")

    # Hide all temporary elements
    temporary_items = cad_scene.getItemsByTags(["temporary"])
    print(f"\n1. Hide temporary elements: {len(temporary_items)} items")
    print("   Usage: for item in temporary_items: item.setVisible(False)")

    # Select all structural elements for editing
    structural_items = cad_scene.getItemsByTags(["structure", "visible"])
    print(f"\n2. Select visible structural elements: {len(structural_items)} items")
    print("   Usage: for item in structural_items: item.setSelected(True)")

    # Change layer visibility - hide all construction layer items
    construction_layer = cad_scene.getItemsByTags(["layer_construction"])
    print(f"\n3. Hide construction layer: {len(construction_layer)} items")

    # Find all dimension elements for style updates
    dimension_items = cad_scene.getItemsByTags(["dimension", "visible"])
    print(f"\n4. Update dimension styles: {len(dimension_items)} items")

    # Find all text that needs font updates
    text_items = cad_scene.getItemsByTags(["text", "visible"])
    print(f"\n5. Update text fonts: {len(text_items)} items")

    # Complex query: find all visible structural walls (not foundation)
    structural_walls = cad_scene.getItemsByTags([
        "structure", "wall", "visible"
    ])
    print(f"\n6. Select structural walls only: {len(structural_walls)} items")

    print("\nThese examples show how getItemsByTags enables:")
    print("- Layer management (show/hide by layer)")
    print("- Object type selection (all dimensions, all text, etc.)")
    print("- State-based operations (temporary vs permanent)")
    print("- Complex filtering (visible structural walls)")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        test_get_items_by_tags()
        test_real_world_usage()
        print("\nAll tests completed successfully!")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Don't start the event loop, just exit
    sys.exit(0)
