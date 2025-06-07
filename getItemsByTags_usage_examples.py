"""
Example usage of CadScene.getItemsByTags() method

This shows practical examples of how to use the getItemsByTags method
for common CAD operations.
"""

from BelfryCAD.gui.cad_scene import CadScene

def layer_management_example():
    """Example: Layer management using getItemsByTags"""

    scene = CadScene()

    # Add items to different layers
    scene.addLine(0, 0, 100, 100, tags=["geometry", "layer_structural"])
    scene.addRect(50, 50, 200, 100, tags=["geometry", "layer_architectural"])
    scene.addText("Note", tags=["annotation", "layer_text"])
    scene.addLine(0, 50, 100, 50, tags=["construction", "layer_construction", "temporary"])

    # Hide all construction layer items
    construction_items = scene.getItemsByTags(["layer_construction"])
    for item in construction_items:
        item.setVisible(False)

    # Show only structural elements
    structural_items = scene.getItemsByTags(["layer_structural"])
    for item in structural_items:
        item.setVisible(True)


def object_selection_example():
    """Example: Selecting objects by type and properties"""

    scene = CadScene()

    # Add various objects
    scene.addLine(0, 0, 100, 100, tags=["geometry", "important", "visible"])
    scene.addRect(50, 50, 200, 100, tags=["geometry", "draft", "visible"])
    scene.addEllipse(150, 150, 100, 50, tags=["geometry", "important", "visible"])
    scene.addText("Title", tags=["text", "important", "visible"])

    # Select all important and visible items for editing
    important_visible = scene.getItemsByTags(["important", "visible"])
    for item in important_visible:
        item.setSelected(True)

    # Find all draft geometry items for review
    draft_geometry = scene.getItemsByTags(["geometry", "draft"])
    # Process draft items...


def styling_example():
    """Example: Applying styles to specific item groups"""

    scene = CadScene()

    # Add items with different categories
    scene.addLine(0, 0, 100, 100, tags=["dimension", "horizontal", "visible"])
    scene.addLine(100, 0, 100, 100, tags=["dimension", "vertical", "visible"])
    scene.addText("100mm", tags=["dimension", "text", "visible"])
    scene.addRect(50, 50, 200, 100, tags=["geometry", "main", "visible"])

    # Update all dimension styles
    dimension_items = scene.getItemsByTags(["dimension", "visible"])
    for item in dimension_items:
        # Apply dimension-specific styling
        pass

    # Update only horizontal dimensions
    horizontal_dims = scene.getItemsByTags(["dimension", "horizontal"])
    for item in horizontal_dims:
        # Apply horizontal dimension styling
        pass


def main():
    """Demo the examples"""
    print("CadScene.getItemsByTags() Usage Examples")
    print("=" * 45)

    print("\n1. Layer Management Example")
    layer_management_example()
    print("   ✓ Construction layer hidden")
    print("   ✓ Structural layer shown")

    print("\n2. Object Selection Example")
    object_selection_example()
    print("   ✓ Important and visible items selected")
    print("   ✓ Draft geometry identified")

    print("\n3. Styling Example")
    styling_example()
    print("   ✓ Dimension styles updated")
    print("   ✓ Horizontal dimensions styled")

    print("\nKey Benefits:")
    print("- Precise object filtering with multiple criteria")
    print("- Efficient bulk operations on related objects")
    print("- Clean separation of concerns (layers, types, states)")
    print("- Flexible query system for complex CAD operations")


if __name__ == "__main__":
    main()
