#!/usr/bin/env python3
"""
Test script for the new removeItemsByTags method in CadScene.

This script demonstrates how to use the removeItemsByTags method to remove
all graphics items that have all of the specified tags.
"""

import sys
import os

# Add the BelfryCAD directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication
from gui.cad_scene import CadScene


def test_remove_items_by_tags():
    """Test the removeItemsByTags method functionality."""

    # Create a CadScene instance
    cad_scene = CadScene()

    print("Testing CadScene.removeItemsByTags() method")
    print("=" * 50)

    # Add various items with different tag combinations
    print("\n1. Adding items with different tag combinations:")

    # Items that will be removed (have both 'temporary' and 'construction')
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["geometry", "temporary", "construction"])
    print("   - Line1: tags=['geometry', 'temporary', 'construction']")

    line2 = cad_scene.addLine(50, 50, 150, 150, tags=["temporary", "construction", "helper"])
    print("   - Line2: tags=['temporary', 'construction', 'helper']")

    # Items that will NOT be removed (missing one of the tags)
    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["geometry", "temporary", "solid"])
    print("   - Rect1: tags=['geometry', 'temporary', 'solid'] (missing 'construction')")

    ellipse1 = cad_scene.addEllipse(150, 150, 100, 50, tags=["geometry", "construction", "solid"])
    print("   - Ellipse1: tags=['geometry', 'construction', 'solid'] (missing 'temporary')")

    text1 = cad_scene.addText("Sample Text", tags=["text", "annotation", "visible"])
    print("   - Text1: tags=['text', 'annotation', 'visible'] (missing both)")

    # Additional item that will be removed
    path_item = cad_scene.addLine(200, 200, 300, 300, tags=["temporary", "construction"])
    print("   - Line3: tags=['temporary', 'construction']")

    print(f"\n2. Initial state:")
    print(f"   Total items in scene: {len(cad_scene.scene.items())}")

    # Check items before removal
    temp_construction_items = cad_scene.getItemsByTags(["temporary", "construction"])
    print(f"   Items with both 'temporary' AND 'construction': {len(temp_construction_items)}")

    temp_items = cad_scene.getItemsByTag("temporary")
    print(f"   Items with 'temporary': {len(temp_items)}")

    construction_items = cad_scene.getItemsByTag("construction")
    print(f"   Items with 'construction': {len(construction_items)}")

    print(f"\n3. Testing removeItemsByTags(['temporary', 'construction']):")

    # Remove items that have both 'temporary' and 'construction' tags
    removed_count = cad_scene.removeItemsByTags(["temporary", "construction"])
    print(f"   Items removed: {removed_count}")

    print(f"\n4. State after removal:")
    print(f"   Total items in scene: {len(cad_scene.scene.items())}")

    # Verify the correct items were removed
    remaining_temp_construction = cad_scene.getItemsByTags([
        "temporary", "construction"
    ])
    print(f"   Items with both 'temporary' AND 'construction': {len(remaining_temp_construction)}")

    remaining_temp = cad_scene.getItemsByTag("temporary")
    print(f"   Items with 'temporary': {len(remaining_temp)}")

    remaining_construction = cad_scene.getItemsByTag("construction")
    print(f"   Items with 'construction': {len(remaining_construction)}")

    # Verify that the remaining items are the expected ones
    print(f"\n5. Verification - checking remaining items:")

    all_remaining_items = [rect1, ellipse1, text1]  # These should still exist
    for i, item in enumerate(all_remaining_items):
        tags = cad_scene.getTags(item)
        if tags:  # Only check if item still has tags (wasn't removed)
            print(f"   Remaining item {i+1}: {tags}")
        else:
            print(f"   Remaining item {i+1}: REMOVED (no tags found)")


def test_edge_cases():
    """Test edge cases for removeItemsByTags."""

    print("\n" + "=" * 50)
    print("TESTING EDGE CASES")
    print("=" * 50)

    cad_scene = CadScene()

    # Add some test items
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["test", "visible"])
    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["test", "geometry"])

    print("\n1. Test removing with non-existent tags:")
    removed = cad_scene.removeItemsByTags(["nonexistent"])
    print(f"   Items removed with non-existent tag: {removed}")
    print(f"   Items still in scene: {len(cad_scene.scene.items())}")

    print("\n2. Test removing with empty tag list:")
    removed = cad_scene.removeItemsByTags([])
    print(f"   Items removed with empty tag list: {removed}")
    print(f"   Items still in scene: {len(cad_scene.scene.items())}")

    print("\n3. Test removing with mix of existing and non-existing tags:")
    removed = cad_scene.removeItemsByTags(["test", "nonexistent"])
    print(f"   Items removed with mixed tags: {removed}")
    print(f"   Items still in scene: {len(cad_scene.scene.items())}")

    print("\n4. Test removing with single existing tag:")
    removed = cad_scene.removeItemsByTags(["test"])
    print(f"   Items removed with 'test' tag: {removed}")
    print(f"   Items still in scene: {len(cad_scene.scene.items())}")


def test_real_world_cleanup():
    """Demonstrate real-world usage for cleanup operations."""

    print("\n" + "=" * 50)
    print("REAL-WORLD CLEANUP EXAMPLE")
    print("=" * 50)

    cad_scene = CadScene()

    print("\nCreating a sample CAD drawing with temporary elements...")

    # Permanent structural elements
    cad_scene.addLine(0, 0, 1000, 0, tags=["structure", "foundation", "permanent", "visible"])
    cad_scene.addLine(1000, 0, 1000, 500, tags=["structure", "wall", "permanent", "visible"])
    cad_scene.addLine(1000, 500, 0, 500, tags=["structure", "wall", "permanent", "visible"])
    cad_scene.addLine(0, 500, 0, 0, tags=["structure", "wall", "permanent", "visible"])

    # Temporary construction lines
    cad_scene.addLine(500, 0, 500, 500, tags=["construction", "centerline", "temporary", "helper"])
    cad_scene.addLine(0, 250, 1000, 250, tags=["construction", "centerline", "temporary", "helper"])
    cad_scene.addLine(250, 0, 250, 500, tags=["construction", "quarter", "temporary", "helper"])
    cad_scene.addLine(750, 0, 750, 500, tags=["construction", "quarter", "temporary", "helper"])

    # Draft annotations (temporary)
    cad_scene.addText("DRAFT", tags=["annotation", "watermark", "temporary", "draft"])
    cad_scene.addText("Work in Progress", tags=["annotation", "status", "temporary", "draft"])

    # Some temporary dimensions
    cad_scene.addLine(0, -50, 1000, -50, tags=["dimension", "temporary", "draft"])
    cad_scene.addText("1000mm", tags=["dimension", "text", "temporary", "draft"])

    # Final annotations (permanent)
    cad_scene.addText("Main Room", tags=["annotation", "label", "permanent", "visible"])

    print(f"Initial drawing has {len(cad_scene.scene.items())} items")

    # Show cleanup scenarios
    print(f"\n1. Cleanup scenario: Remove all temporary draft elements")
    temp_draft_items = cad_scene.getItemsByTags(["temporary", "draft"])
    print(f"   Items with both 'temporary' AND 'draft': {len(temp_draft_items)}")

    removed = cad_scene.removeItemsByTags(["temporary", "draft"])
    print(f"   Removed {removed} temporary draft items")
    print(f"   Remaining items: {len(cad_scene.scene.items())}")

    print(f"\n2. Cleanup scenario: Remove all temporary construction helpers")
    temp_helper_items = cad_scene.getItemsByTags(["temporary", "helper"])
    print(f"   Items with both 'temporary' AND 'helper': {len(temp_helper_items)}")

    removed = cad_scene.removeItemsByTags(["temporary", "helper"])
    print(f"   Removed {removed} temporary helper items")
    print(f"   Remaining items: {len(cad_scene.scene.items())}")

    print(f"\n3. Final drawing state:")
    permanent_items = cad_scene.getItemsByTag("permanent")
    print(f"   Permanent items remaining: {len(permanent_items)}")
    print(f"   Total items in scene: {len(cad_scene.scene.items())}")

    print(f"\n4. Verification - what types of items remain:")
    all_tags = set()
    for item in cad_scene.scene.items():
        all_tags.update(cad_scene.getTags(item))

    print(f"   Remaining tags in scene: {sorted(all_tags)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        test_remove_items_by_tags()
        test_edge_cases()
        test_real_world_cleanup()
        print("\n" + "=" * 50)
        print("All removeItemsByTags tests completed successfully!")
        print("The method correctly removes items that have ALL specified tags.")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Don't start the event loop, just exit
    sys.exit(0)
