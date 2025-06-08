#!/usr/bin/env python3
"""
Test script to verify CadScene's multi-tag system functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))


def test_multi_tag_system():
    """Test the multi-tag system functionality."""
    print("Testing CadScene multi-tag system...")

    # Test import
    try:
        from BelfryCAD.gui.cad_scene import CadScene
        print("✓ CadScene import successful")
    except Exception as e:
        print(f"✗ CadScene import failed: {e}")
        return False

    # Test multi-tag functionality (without Qt dependencies)
    try:
        # Create a mock scene instance
        scene = CadScene.__new__(CadScene)
        scene._tagged_items = {}
        scene._item_tags = {}

        # Create a mock graphics item that simulates QGraphicsItem
        class MockItem:
            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return f"MockItem({self.name})"

        item = MockItem("test_item")

        # Test the tag application methods
        scene.addTag(item, "tag1")
        scene.addTag(item, "tag2")
        scene.addTag(item, "tag3")

        # Test add_tags method
        scene.addTags(item, ["tag4", "tag5"])

        # Verify tags were applied
        tags = scene.getTags(item)
        expected_tags = ["tag1", "tag2", "tag3", "tag4", "tag5"]

        if set(tags) == set(expected_tags):
            print("✓ Multi-tag application successful")
            print(f"  Applied tags: {tags}")
        else:
            print(f"✗ Multi-tag application failed.")
            print(f"  Expected {expected_tags}, got {tags}")
            return False

        # Test tag retrieval
        items_with_tag1 = scene.getItemsByTag("tag1")
        if item in items_with_tag1:
            print("✓ Tag retrieval successful")
        else:
            print("✗ Tag retrieval failed")
            return False

        # Test tag removal
        scene.removeTag(item, "tag2")
        remaining_tags = scene.getTags(item)
        if "tag2" not in remaining_tags and len(remaining_tags) == 4:
            print("✓ Tag removal successful")
        else:
            print(f"✗ Tag removal failed. Remaining tags: {remaining_tags}")
            return False

        # Test clear all tags
        scene.clearAllTags()
        if len(scene.getTags(item)) == 0:
            print("✓ Clear all tags successful")
        else:
            print("✗ Clear all tags failed")
            return False

        print("✓ All multi-tag system tests passed!")
        return True

    except Exception as e:
        print(f"✗ Multi-tag system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_signatures():
    """Test that all add* methods have the correct signatures."""
    print("\nTesting method signatures...")

    try:
        from BelfryCAD.gui.cad_scene import CadScene
        import inspect

        # List of methods to check
        methods_to_check = [
            'addItem', 'addLine', 'addRect', 'addEllipse',
            'addPolygon', 'addPixmap', 'addPath', 'addText'
        ]

        for method_name in methods_to_check:
            if hasattr(CadScene, method_name):
                method = getattr(CadScene, method_name)
                signature = inspect.signature(method)

                # Check if 'tags' parameter exists and is optional
                if 'tags' in signature.parameters:
                    param = signature.parameters['tags']
                    if param.default is None:
                        print(f"✓ {method_name} has correct 'tags' parameter")
                    else:
                        msg = f"✗ {method_name} 'tags' parameter default"
                        msg += " is not None"
                        print(msg)
                        return False
                else:
                    print(f"✗ {method_name} missing 'tags' parameter")
                    return False
            else:
                print(f"✗ {method_name} method not found")
                return False

        print("✓ All method signatures are correct!")
        return True

    except Exception as e:
        print(f"✗ Method signature test failed: {e}")
        return False


if __name__ == "__main__":
    print("CadScene Multi-Tag System Test")
    print("=" * 40)

    success1 = test_multi_tag_system()
    success2 = test_method_signatures()

    if success1 and success2:
        msg = "\n🎉 All tests passed! CadScene multi-tag system"
        msg += " is working correctly."
        print(msg)
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
