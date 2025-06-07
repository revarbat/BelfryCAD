#!/usr/bin/env python3
"""
Test script to verify the tagging system implementation is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsEllipseItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush, QColor

from BelfryCAD.gui.drawing_manager import (
    DrawingManager, DrawingContext, DrawingTags
)
from BelfryCAD.gui.cad_scene import CadScene


def test_tagging_system():
    """Test the tagging system functionality"""
    print("Testing DrawingManager tagging system...")

    # Create Qt application (needed for graphics items)
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    # Create scene and context
    scene = QGraphicsScene()
    context = DrawingContext(scene=scene)
    drawing_manager = DrawingManager(context)

    # Create CadScene with the same scene and link it to the DrawingManager
    cad_scene = CadScene()
    cad_scene.scene = scene  # Use the same scene
    drawing_manager.set_cad_scene(cad_scene)

    # Create some test graphics items
    item1 = scene.addEllipse(0, 0, 10, 10, QPen(QColor("red")), QBrush(Qt.BrushStyle.NoBrush))
    item2 = scene.addEllipse(20, 20, 15, 15, QPen(QColor("blue")), QBrush(Qt.BrushStyle.NoBrush))
    item3 = scene.addRect(40, 40, 10, 10, QPen(QColor("green")), QBrush(Qt.BrushStyle.NoBrush))

    print("✓ Created test graphics items")

    # Test adding tags
    drawing_manager.add_item_tag(item1, "circle")
    drawing_manager.add_item_tag(item1, "red")
    drawing_manager.add_item_tag(item1, DrawingTags.ALL_DRAWN.value)

    drawing_manager.add_item_tag(item2, "circle")
    drawing_manager.add_item_tag(item2, "blue")
    drawing_manager.add_item_tag(item2, DrawingTags.ALL_DRAWN.value)

    drawing_manager.add_item_tag(item3, "rectangle")
    drawing_manager.add_item_tag(item3, "green")
    drawing_manager.add_item_tag(item3, DrawingTags.ALL_DRAWN.value)

    print("✓ Added tags to items")

    # Test retrieving items by tag
    circles = drawing_manager.get_items_by_tag("circle")
    all_drawn = drawing_manager.get_items_by_tag(DrawingTags.ALL_DRAWN.value)
    red_items = drawing_manager.get_items_by_tag("red")

    assert len(circles) == 2, f"Expected 2 circles, got {len(circles)}"
    assert len(all_drawn) == 3, f"Expected 3 all_drawn items, got {len(all_drawn)}"
    assert len(red_items) == 1, f"Expected 1 red item, got {len(red_items)}"

    print("✓ Retrieved items by single tag correctly")

    # Test retrieving items by multiple tags (ANY)
    any_color = drawing_manager.get_items_by_any_tag(["red", "blue"])
    assert len(any_color) == 2, f"Expected 2 colored items, got {len(any_color)}"

    print("✓ Retrieved items by any tag correctly")

    # Test retrieving items by multiple tags (ALL)
    red_circles = drawing_manager.get_items_by_all_tags(["circle", "red"])
    blue_circles = drawing_manager.get_items_by_all_tags(["circle", "blue"])

    assert len(red_circles) == 1, f"Expected 1 red circle, got {len(red_circles)}"
    assert len(blue_circles) == 1, f"Expected 1 blue circle, got {len(blue_circles)}"

    print("✓ Retrieved items by all tags correctly")

    # Test getting tags from item
    item1_tags = drawing_manager.get_item_tags(item1)
    expected_tags = {"circle", "red", DrawingTags.ALL_DRAWN.value}
    actual_tags = set(item1_tags)

    assert actual_tags == expected_tags, f"Expected {expected_tags}, got {actual_tags}"

    print("✓ Retrieved tags from item correctly")

    # Test removing tags
    drawing_manager.remove_item_tag(item1, "red")
    item1_tags_after = drawing_manager.get_item_tags(item1)

    assert "red" not in item1_tags_after, "Red tag should be removed"
    assert "circle" in item1_tags_after, "Circle tag should remain"

    print("✓ Removed tag correctly")
    
    # Debug: Check current circle items and their tags
    current_circles = drawing_manager.get_items_by_tag("circle")
    print(f"Current circles: {len(current_circles)}")
    for i, circle in enumerate(current_circles):
        tags = drawing_manager.get_item_tags(circle)
        print(f"  Circle {i+1} tags: {tags}")

    # Test removing items by tag
    initial_scene_count = len(scene.items())
    print(f"Initial scene count: {initial_scene_count}")
    
    circles_before = drawing_manager.get_items_by_tag("circle")
    print(f"Circles before removal: {len(circles_before)}")
    
    drawing_manager.remove_items_by_tag("circle")
    
    final_scene_count = len(scene.items())
    print(f"Final scene count: {final_scene_count}")
    
    circles_after = drawing_manager.get_items_by_tag("circle")
    print(f"Circles after removal: {len(circles_after)}")

    assert final_scene_count == initial_scene_count - 2, "Should have removed 2 circle items"

    print("✓ Removed items by tag correctly")

    # Test clearing all tags
    drawing_manager.clearAllTags()
    remaining_tags = drawing_manager.get_items_by_tag(DrawingTags.ALL_DRAWN.value)

    assert len(remaining_tags) == 0, "All tags should be cleared"

    print("✓ Cleared all tags correctly")

    print("\n🎉 All tagging system tests passed successfully!")
    return True


if __name__ == "__main__":
    try:
        test_tagging_system()
        print("\n✅ TAGGING SYSTEM IMPLEMENTATION COMPLETE")
        print("The tagging system is fully functional and ready for use.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
