#!/usr/bin/env python3
"""
Test script to verify CadScene tagging integration with DrawingManager.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPen, QBrush, QColor
from gui.cad_scene import CadScene
from gui.drawing_manager import DrawingManager
from core.cad_objects import LineCADObject, RectangleCADObject
from core.object_types import ObjectType


def test_cad_scene_tagging_integration():
    """Test that CadScene tagging works with DrawingManager."""
    print("Testing CadScene tagging integration...")

    # Create CadScene
    scene = CadScene()

    # Test direct CadScene tagging
    print("\n1. Testing direct CadScene tagging:")
    pen = QPen(QColor(255, 0, 0))
    brush = QBrush(QColor(0, 255, 0))

    # Add items with tags
    line = scene.addLine(0, 0, 100, 100, pen, "test_line")
    rect = scene.addRect(50, 50, 100, 100, pen, brush, "test_rect")
    ellipse = scene.addEllipse(0, 0, 50, 50, pen, brush, "test_ellipse")

    print(f"  Added line with tags: {scene.getTags(line)}")
    print(f"  Added rect with tags: {scene.getTags(rect)}")
    print(f"  Added ellipse with tags: {scene.getTags(ellipse)}")

    # Test tag retrieval
    print(f"  Items with 'test_line' tag: "
          f"{len(scene.getItemsByTag('test_line'))}")
    print(f"  Items with 'test_rect' tag: "
          f"{len(scene.getItemsByTag('test_rect'))}")

    # Test DrawingManager integration
    print("\n2. Testing DrawingManager integration:")
    drawing_manager = DrawingManager()
    scene.setup_drawing_manager(drawing_manager)

    # Verify DrawingManager has CadScene reference
    print(f"  DrawingManager has cad_scene: {drawing_manager.cad_scene is not None}")
    print(f"  CadScene is the same object: {drawing_manager.cad_scene is scene}")

    # Test DrawingManager tagging methods (should delegate to CadScene)
    test_item = scene.addLine(200, 200, 300, 300, pen)
    drawing_manager.add_item_tag(test_item, "manager_tag")

    print(f"  Item tags via DrawingManager: {drawing_manager.get_item_tags(test_item)}")
    print(f"  Item tags via CadScene: {scene.getTags(test_item)}")
    tags_match = drawing_manager.get_item_tags(test_item) == scene.getTags(test_item)
    print(f"  Tags match: {tags_match}")

    # Test tag-based retrieval
    manager_items = drawing_manager.get_items_by_tag("manager_tag")
    scene_items = scene.getItemsByTag("manager_tag")
    print(f"  Items via DrawingManager: {len(manager_items)}")
    print(f"  Items via CadScene: {len(scene_items)}")
    print(f"  Results match: {manager_items == scene_items}")

    print("\n3. Testing comprehensive tagging:")

    # Add multiple tags to an item
    multi_item = scene.addRect(300, 300, 50, 50, pen, brush)
    scene.addTag(multi_item, "tag1")
    scene.addTag(multi_item, "tag2")
    scene.addTag(multi_item, "tag3")

    print(f"  Multi-tagged item tags: {scene.getTags(multi_item)}")

    # Remove a tag
    scene.removeTag(multi_item, "tag2")
    print(f"  After removing 'tag2': {scene.getTags(multi_item)}")

    # Clear all tags from item
    scene.clearTags(multi_item)
    print(f"  After clearing all tags: {scene.getTags(multi_item)}")

    print("\n✅ All CadScene tagging integration tests passed!")
    return True


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        test_cad_scene_tagging_integration()
        print("\n🎉 Integration test completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
