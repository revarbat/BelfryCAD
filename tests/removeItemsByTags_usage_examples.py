"""
Usage examples for CadScene.removeItemsByTags() method

This demonstrates practical examples of how to use the removeItemsByTags method
for common CAD cleanup and management operations.
"""

from BelfryCAD.gui.cad_scene import CadScene

def cleanup_temporary_elements_example():
    """Example: Remove all temporary construction elements"""

    scene = CadScene()

    # Add permanent structural elements
    scene.addLine(0, 0, 1000, 0, tags=["structure", "foundation", "permanent"])
    scene.addRect(100, 100, 800, 300, tags=["structure", "room", "permanent"])

    # Add temporary construction lines
    scene.addLine(500, 0, 500, 400, tags=["construction", "temporary", "centerline"])
    scene.addLine(0, 200, 1000, 200, tags=["construction", "temporary", "centerline"])
    scene.addLine(250, 0, 250, 400, tags=["construction", "temporary", "helper"])

    # Add temporary draft annotations
    scene.addText("DRAFT", tags=["annotation", "temporary", "watermark"])
    scene.addText("Work in Progress", tags=["annotation", "temporary", "status"])

    print(f"Before cleanup: {len(scene.scene.items())} items in scene")

    # Clean up all temporary construction elements
    removed = scene.removeItemsByTags(["construction", "temporary"])
    print(f"Removed {removed} temporary construction items")

    # Clean up all temporary annotations
    removed = scene.removeItemsByTags(["annotation", "temporary"])
    print(f"Removed {removed} temporary annotation items")

    print(f"After cleanup: {len(scene.scene.items())} items in scene")


def layer_cleanup_example():
    """Example: Remove items from specific layers with specific properties"""

    scene = CadScene()

    # Add items to different layers with different states
    scene.addLine(0, 0, 100, 100, tags=["layer_sketch", "draft", "hidden"])
    scene.addRect(50, 50, 200, 100, tags=["layer_sketch", "draft", "visible"])
    scene.addEllipse(150, 150, 100, 50, tags=["layer_design", "final", "visible"])
    scene.addText("Note", tags=["layer_notes", "draft", "visible"])
    scene.addLine(200, 200, 300, 300, tags=["layer_sketch", "final", "visible"])

    print(f"Initial: {len(scene.scene.items())} items")

    # Remove all hidden draft items from sketch layer
    removed = scene.removeItemsByTags(["layer_sketch", "draft", "hidden"])
    print(f"Removed {removed} hidden sketch draft items")

    # Remove all draft items (regardless of layer)
    # Note: This will remove visible draft items too
    remaining_draft = scene.getItemsByTags(["draft"])
    print(f"Remaining draft items before cleanup: {len(remaining_draft)}")

    removed = scene.removeItemsByTags(["draft"])
    print(f"Removed {removed} remaining draft items")

    print(f"Final: {len(scene.scene.items())} items")


def progressive_cleanup_example():
    """Example: Progressive cleanup with multiple criteria"""

    scene = CadScene()

    # Create a complex drawing with multiple tag combinations
    scene.addLine(0, 0, 100, 100, tags=["geometry", "construction", "temporary", "old"])
    scene.addRect(50, 50, 200, 100, tags=["geometry", "construction", "temporary", "new"])
    scene.addEllipse(150, 150, 100, 50, tags=["geometry", "design", "permanent", "new"])
    scene.addText("Old Note", tags=["annotation", "note", "temporary", "old"])
    scene.addText("New Note", tags=["annotation", "note", "permanent", "new"])
    scene.addLine(200, 200, 300, 300, tags=["dimension", "construction", "temporary", "old"])

    print(f"Starting with: {len(scene.scene.items())} items")

    # Step 1: Remove old temporary construction items
    removed = scene.removeItemsByTags(["construction", "temporary", "old"])
    print(f"Step 1 - Removed {removed} old temporary construction items")
    print(f"Remaining: {len(scene.scene.items())} items")

    # Step 2: Remove any remaining temporary items (old or new)
    removed = scene.removeItemsByTags(["temporary"])
    print(f"Step 2 - Removed {removed} remaining temporary items")
    print(f"Remaining: {len(scene.scene.items())} items")

    # Step 3: Show what's left
    remaining_items = scene.scene.items()
    print(f"Final cleanup complete: {len(remaining_items)} permanent items remain")

    # List remaining item types
    remaining_tags = set()
    for item in remaining_items:
        if hasattr(item, '_tags'):  # Skip grid items that might not have tags
            remaining_tags.update(scene.getTags(item))

    if remaining_tags:
        print(f"Remaining tag types: {sorted(remaining_tags)}")


def bulk_operations_example():
    """Example: Using removeItemsByTags for bulk operations"""

    scene = CadScene()

    # Create items that need bulk operations
    for i in range(5):
        scene.addLine(i*50, 0, i*50+50, 100, tags=["test_batch", "geometry", "generated"])
        scene.addRect(i*50, 100, 40, 40, tags=["test_batch", "geometry", "generated"])

    # Add some items that should NOT be removed
    scene.addLine(300, 0, 400, 100, tags=["test_batch", "geometry", "manual"])
    scene.addText("Keep This", tags=["annotation", "important", "manual"])

    print(f"Created test batch: {len(scene.scene.items())} total items")

    # Count items before removal
    generated_items = scene.getItemsByTags(["test_batch", "generated"])
    print(f"Generated items to remove: {len(generated_items)}")

    # Remove all generated test batch items
    removed = scene.removeItemsByTags(["test_batch", "generated"])
    print(f"Bulk removed {removed} generated items")

    # Verify manual items remain
    manual_items = scene.getItemsByTags(["manual"])
    print(f"Manual items remaining: {len(manual_items)}")

    print(f"Final total: {len(scene.scene.items())} items")


def main():
    """Demo all the examples"""
    print("CadScene.removeItemsByTags() Usage Examples")
    print("=" * 50)

    print("\n1. Cleanup Temporary Elements")
    print("-" * 30)
    cleanup_temporary_elements_example()

    print("\n2. Layer Cleanup")
    print("-" * 30)
    layer_cleanup_example()

    print("\n3. Progressive Cleanup")
    print("-" * 30)
    progressive_cleanup_example()

    print("\n4. Bulk Operations")
    print("-" * 30)
    bulk_operations_example()

    print("\n" + "=" * 50)
    print("Key Benefits of removeItemsByTags:")
    print("- Clean up complex scenes with precise criteria")
    print("- Remove temporary elements after design completion")
    print("- Bulk delete operations on tagged item groups")
    print("- Progressive cleanup with multiple filtering steps")
    print("- Automated cleanup workflows in CAD applications")


if __name__ == "__main__":
    main()
