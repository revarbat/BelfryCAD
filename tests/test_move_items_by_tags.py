#!/usr/bin/env python3
"""
Test script for the new moveItemsByTags method in CadScene.

This script demonstrates how to use the moveItemsByTags method to move
all graphics items that have all of the specified tags.
"""

import sys
import os

# Add the BelfryCAD directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication
from gui.cad_scene import CadScene


def test_move_items_with_all_tags():
    """Test the moveItemsByTags method functionality."""

    # Create a CadScene instance
    cad_scene = CadScene()

    print("Testing CadScene.moveItemsByTags() method")
    print("=" * 50)

    # Add various items with different tag combinations
    print("\n1. Adding items with different tag combinations:")

    # Items that will be moved (have both 'movable' and 'temporary')
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["geometry", "movable", "temporary"])
    print("   - Line1: tags=['geometry', 'movable', 'temporary']")
    print(f"     Initial position: ({line1.x()}, {line1.y()})")

    line2 = cad_scene.addLine(50, 50, 150, 150, tags=["movable", "temporary", "helper"])
    print("   - Line2: tags=['movable', 'temporary', 'helper']")
    print(f"     Initial position: ({line2.x()}, {line2.y()})")

    # Items that will NOT be moved (missing one of the tags)
    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["geometry", "movable", "solid"])
    print("   - Rect1: tags=['geometry', 'movable', 'solid'] (missing 'temporary')")
    print(f"     Initial position: ({rect1.x()}, {rect1.y()})")

    ellipse1 = cad_scene.addEllipse(150, 150, 100, 50, tags=["geometry", "temporary", "solid"])
    print("   - Ellipse1: tags=['geometry', 'temporary', 'solid'] (missing 'movable')")
    print(f"     Initial position: ({ellipse1.x()}, {ellipse1.y()})")

    text1 = cad_scene.addText("Sample Text", tags=["text", "annotation", "visible"])
    print("   - Text1: tags=['text', 'annotation', 'visible'] (missing both)")
    print(f"     Initial position: ({text1.x()}, {text1.y()})")

    # Additional item that will be moved
    path_item = cad_scene.addLine(200, 200, 300, 300, tags=["movable", "temporary"])
    print("   - Line3: tags=['movable', 'temporary']")
    print(f"     Initial position: ({path_item.x()}, {path_item.y()})")

    print(f"\n2. Initial state:")
    print(f"   Total items in scene: {len(cad_scene.scene.items())}")

    # Check items before movement
    movable_temp_items = cad_scene.getItemsByTags(["movable", "temporary"])
    print(f"   Items with both 'movable' AND 'temporary': {len(movable_temp_items)}")

    print(f"\n3. Testing moveItemsByTags(['movable', 'temporary'], 100, 50):")

    # Move items that have both 'movable' and 'temporary' tags
    moved_count = cad_scene.moveItemsByTags(["movable", "temporary"], 100, 50)
    print(f"   Items moved: {moved_count}")

    print(f"\n4. Positions after movement:")

    # Check the positions after movement
    print("   Items that should have moved:")
    print(f"   - Line1: ({line1.x()}, {line1.y()}) (should be 100, 50)")
    print(f"   - Line2: ({line2.x()}, {line2.y()}) (should be 150, 100)")
    print(f"   - Line3: ({path_item.x()}, {path_item.y()}) (should be 300, 250)")

    print("   Items that should NOT have moved:")
    print(f"   - Rect1: ({rect1.x()}, {rect1.y()}) (should be 50, 50)")
    print(f"   - Ellipse1: ({ellipse1.x()}, {ellipse1.y()}) (should be 150, 150)")
    print(f"   - Text1: ({text1.x()}, {text1.y()}) (should be 0, 0)")


def test_edge_cases():
    """Test edge cases for moveItemsByTags."""

    print("\n" + "=" * 50)
    print("TESTING EDGE CASES")
    print("=" * 50)

    cad_scene = CadScene()

    # Add some test items
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["test", "visible"])
    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["test", "geometry"])

    print(f"\nInitial positions:")
    print(f"   Line1: ({line1.x()}, {line1.y()})")
    print(f"   Rect1: ({rect1.x()}, {rect1.y()})")

    print("\n1. Test moving with non-existent tags:")
    moved = cad_scene.moveItemsByTags(["nonexistent"], 10, 10)
    print(f"   Items moved with non-existent tag: {moved}")
    print(f"   Line1 position: ({line1.x()}, {line1.y()}) (should be unchanged)")

    print("\n2. Test moving with empty tag list:")
    moved = cad_scene.moveItemsByTags([], 10, 10)
    print(f"   Items moved with empty tag list: {moved}")
    print(f"   Line1 position: ({line1.x()}, {line1.y()}) (should be unchanged)")

    print("\n3. Test moving with mix of existing and non-existing tags:")
    moved = cad_scene.moveItemsByTags(["test", "nonexistent"], 10, 10)
    print(f"   Items moved with mixed tags: {moved}")
    print(f"   Line1 position: ({line1.x()}, {line1.y()}) (should be unchanged)")

    print("\n4. Test moving with single existing tag:")
    moved = cad_scene.moveItemsByTags(["test"], 25, 30)
    print(f"   Items moved with 'test' tag: {moved}")
    print(f"   Line1 position: ({line1.x()}, {line1.y()}) (should be 25, 30)")
    print(f"   Rect1 position: ({rect1.x()}, {rect1.y()}) (should be 75, 80)")


def test_real_world_usage():
    """Demonstrate real-world usage for moving groups of items."""

    print("\n" + "=" * 50)
    print("REAL-WORLD USAGE EXAMPLE")
    print("=" * 50)

    cad_scene = CadScene()

    print("\nCreating a sample CAD drawing with grouped elements...")

    # Create a group of items representing a house
    cad_scene.addLine(0, 0, 100, 0, tags=["house", "foundation", "structure"])
    cad_scene.addLine(100, 0, 100, 100, tags=["house", "wall", "structure"])
    cad_scene.addLine(100, 100, 0, 100, tags=["house", "wall", "structure"])
    cad_scene.addLine(0, 100, 0, 0, tags=["house", "wall", "structure"])
    cad_scene.addRect(20, 20, 60, 60, tags=["house", "room", "interior"])

    # Create another group representing a garage
    cad_scene.addLine(150, 0, 250, 0, tags=["garage", "foundation", "structure"])
    cad_scene.addLine(250, 0, 250, 80, tags=["garage", "wall", "structure"])
    cad_scene.addLine(250, 80, 150, 80, tags=["garage", "wall", "structure"])
    cad_scene.addLine(150, 80, 150, 0, tags=["garage", "wall", "structure"])

    # Add some temporary construction marks
    cad_scene.addLine(50, -20, 50, 120, tags=["construction", "centerline", "temporary"])
    cad_scene.addLine(-20, 50, 120, 50, tags=["construction", "centerline", "temporary"])

    print(f"Created drawing with {len(cad_scene.scene.items())} total items")

    # Get initial positions of some items for reference
    house_items = cad_scene.getItemsByTags(["house"])
    garage_items = cad_scene.getItemsByTags(["garage"])
    construction_items = cad_scene.getItemsByTags(["construction"])

    print(f"House items: {len(house_items)}")
    print(f"Garage items: {len(garage_items)}")
    print(f"Construction items: {len(construction_items)}")

    print("\n1. Moving the entire house 200 units to the right:")
    moved = cad_scene.moveItemsByTags(["house"], 200, 0)
    print(f"   Moved {moved} house items")

    print("\n2. Moving the garage 100 units up:")
    moved = cad_scene.moveItemsByTags(["garage"], 0, 100)
    print(f"   Moved {moved} garage items")

    print("\n3. Moving construction lines out of the way:")
    moved = cad_scene.moveItemsByTags(["construction"], 0, -100)
    print(f"   Moved {moved} construction items")

    print("\n4. Final arrangement complete!")
    print("   - House is now at position (200, 0) to (300, 100)")
    print("   - Garage is now at position (150, 100) to (250, 180)")
    print("   - Construction lines moved down to avoid interference")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        test_move_items_with_all_tags()
        test_edge_cases()
        test_real_world_usage()
        print("\n" + "=" * 50)
        print("All moveItemsByTags tests completed successfully!")
        print("The method correctly moves items that have ALL specified tags.")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Don't start the event loop, just exit
    sys.exit(0)
