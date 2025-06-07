"""
Usage examples for CadScene.moveItemsByTags() method

This demonstrates practical examples of how to use the moveItemsByTags method
for common CAD operations like moving groups of objects, aligning elements, and
positioning tagged components.
"""

from PySide6.QtWidgets import QApplication
import sys
from BelfryCAD.gui.cad_scene import CadScene

def group_movement_example():
    """Example: Move entire groups of related items"""
    
    scene = CadScene()
    
    # Create a complex drawing with multiple groups
    # Main building structure
    scene.addRect(0, 0, 200, 150, tags=["building", "main", "structure"])
    scene.addLine(0, 0, 200, 0, tags=["building", "main", "foundation"])
    scene.addLine(200, 0, 200, 150, tags=["building", "main", "wall"])
    scene.addLine(200, 150, 0, 150, tags=["building", "main", "wall"])
    scene.addLine(0, 150, 0, 0, tags=["building", "main", "wall"])
    
    # Annex building
    scene.addRect(250, 0, 100, 100, tags=["building", "annex", "structure"])
    scene.addLine(250, 0, 350, 0, tags=["building", "annex", "foundation"])
    scene.addLine(350, 0, 350, 100, tags=["building", "annex", "wall"])
    scene.addLine(350, 100, 250, 100, tags=["building", "annex", "wall"])
    scene.addLine(250, 100, 250, 0, tags=["building", "annex", "wall"])
    
    # Landscaping elements
    scene.addEllipse(50, 200, 30, 30, tags=["landscape", "tree", "decoration"])
    scene.addEllipse(300, 200, 25, 25, tags=["landscape", "tree", "decoration"])
    scene.addRect(0, 250, 400, 50, tags=["landscape", "path", "decoration"])
    
    print(f"Initial drawing: {len(scene.scene.items())} items")
    
    # Move the entire main building 50 units right and 25 units up
    print("\n1. Moving main building...")
    main_items = scene.getItemsByTags(["building", "main"])
    print(f"   Main building items: {len(main_items)}")
    moved = scene.moveItemsByTags(["building", "main"], 50, 25)
    print(f"   Moved {moved} main building items")
    
    # Move the annex building to align with the main building
    print("\n2. Moving annex building...")
    annex_items = scene.getItemsByTags(["building", "annex"])
    print(f"   Annex building items: {len(annex_items)}")
    moved = scene.moveItemsByTags(["building", "annex"], 50, 25)
    print(f"   Moved {moved} annex building items")
    
    # Move all landscaping elements
    print("\n3. Moving landscaping...")
    landscape_items = scene.getItemsByTags(["landscape"])
    print(f"   Landscape items: {len(landscape_items)}")
    moved = scene.moveItemsByTags(["landscape"], 0, -50)
    print(f"   Moved {moved} landscape items")
    
    print("\nResult: Entire site layout repositioned while maintaining relationships")


def alignment_example():
    """Example: Align groups of items using moveItemsByTags"""
    
    scene = CadScene()
    
    # Create misaligned elements that need to be positioned
    scene.addRect(10, 10, 80, 60, tags=["component", "widget", "ui"])
    scene.addText("Button 1", tags=["component", "widget", "ui", "text"])
    
    scene.addRect(15, 90, 70, 50, tags=["component", "widget", "ui"])
    scene.addText("Button 2", tags=["component", "widget", "ui", "text"])
    
    scene.addRect(5, 160, 90, 40, tags=["component", "widget", "ui"])
    scene.addText("Button 3", tags=["component", "widget", "ui", "text"])
    
    # Add some labels that shouldn't move
    scene.addText("UI Layout", tags=["label", "title", "fixed"])
    scene.addText("Version 1.0", tags=["label", "version", "fixed"])
    
    print(f"Created UI layout with {len(scene.scene.items())} items")
    
    # Move all UI components to align them
    print("\n1. Aligning UI components...")
    ui_items = scene.getItemsByTags(["component", "ui"])
    print(f"   UI component items: {len(ui_items)}")
    
    # Move everything to start at X=50 (align left edges)
    moved = scene.moveItemsByTags(["component", "ui"], 40, 0)
    print(f"   Moved {moved} UI components for alignment")
    
    # Labels should remain in place
    label_items = scene.getItemsByTags(["label"])
    print(f"   Fixed labels: {len(label_items)} (should not have moved)")
    
    print("Result: UI components aligned while preserving fixed labels")


def layer_positioning_example():
    """Example: Position items by layer using tags"""
    
    scene = CadScene()
    
    # Create items on different layers
    # Layer 1 - Mechanical
    scene.addLine(0, 0, 100, 0, tags=["layer1", "mechanical", "structure"])
    scene.addLine(100, 0, 100, 100, tags=["layer1", "mechanical", "structure"])
    scene.addRect(20, 20, 60, 60, tags=["layer1", "mechanical", "component"])
    
    # Layer 2 - Electrical
    scene.addLine(10, 10, 90, 10, tags=["layer2", "electrical", "wire"])
    scene.addLine(10, 90, 90, 90, tags=["layer2", "electrical", "wire"])
    scene.addEllipse(40, 40, 20, 20, tags=["layer2", "electrical", "component"])
    
    # Layer 3 - Annotations
    scene.addText("Motor", tags=["layer3", "annotation", "label"])
    scene.addText("Control", tags=["layer3", "annotation", "label"])
    
    print(f"Created multi-layer drawing: {len(scene.scene.items())} items")
    
    # Separate layers by moving them to different positions
    print("\n1. Separating layers for review...")
    
    # Keep layer 1 in place (reference)
    layer1_items = scene.getItemsByTags(["layer1"])
    print(f"   Layer 1 (mechanical): {len(layer1_items)} items - keeping in place")
    
    # Move layer 2 to the right
    layer2_items = scene.getItemsByTags(["layer2"])
    print(f"   Layer 2 (electrical): {len(layer2_items)} items")
    moved = scene.moveItemsByTags(["layer2"], 150, 0)
    print(f"   Moved {moved} electrical items to the right")
    
    # Move layer 3 below
    layer3_items = scene.getItemsByTags(["layer3"])
    print(f"   Layer 3 (annotations): {len(layer3_items)} items")
    moved = scene.moveItemsByTags(["layer3"], 0, 150)
    print(f"   Moved {moved} annotation items below")
    
    print("Result: Layers separated for independent review and editing")


def precision_positioning_example():
    """Example: Precise positioning of tagged components"""
    
    scene = CadScene()
    
    # Create components that need precise positioning
    scene.addRect(0, 0, 50, 50, tags=["precision", "component", "part1"])
    scene.addRect(10, 10, 30, 30, tags=["precision", "component", "part2"])
    scene.addLine(25, 0, 25, 50, tags=["precision", "centerline", "part1"])
    
    scene.addEllipse(100, 100, 40, 40, tags=["precision", "component", "part3"])
    scene.addLine(120, 100, 120, 140, tags=["precision", "centerline", "part3"])
    
    # Create reference grid
    for i in range(0, 200, 50):
        scene.addLine(i, -10, i, 200, tags=["grid", "reference", "guide"])
        scene.addLine(-10, i, 200, i, tags=["grid", "reference", "guide"])
    
    print(f"Created precision layout: {len(scene.scene.items())} items")
    
    # Move components to exact grid positions
    print("\n1. Positioning components on grid...")
    
    # Move part1 to exact position (0, 0) - already there
    part1_items = scene.getItemsByTags(["precision", "part1"])
    print(f"   Part1: {len(part1_items)} items already at origin")
    
    # Move part2 to precise offset from part1
    part2_items = scene.getItemsByTags(["precision", "part2"])
    print(f"   Part2: {len(part2_items)} items")
    moved = scene.moveItemsByTags(["precision", "part2"], 5, 5)
    print(f"   Moved {moved} part2 items to precise offset")
    
    # Move part3 to exact grid intersection
    part3_items = scene.getItemsByTags(["precision", "part3"])
    print(f"   Part3: {len(part3_items)} items")
    moved = scene.moveItemsByTags(["precision", "part3"], -50, -50)
    print(f"   Moved {moved} part3 items to grid intersection (50, 50)")
    
    print("Result: All components positioned with precision on the grid")


def main():
    """Demo all the examples"""
    print("CadScene.moveItemsByTags() Usage Examples")
    print("=" * 50)
    
    print("\n1. Group Movement")
    print("-" * 30)
    group_movement_example()
    
    print("\n2. Alignment Operations")
    print("-" * 30)
    alignment_example()
    
    print("\n3. Layer Positioning")
    print("-" * 30)
    layer_positioning_example()
    
    print("\n4. Precision Positioning")
    print("-" * 30)
    precision_positioning_example()
    
    print("\n" + "=" * 50)
    print("Key Benefits of moveItemsByTags:")
    print("- Move entire groups of related items as a unit")
    print("- Maintain relative positioning within groups")
    print("- Align components using tag-based selection")
    print("- Separate layers for independent editing")
    print("- Precise positioning with coordinate offsets")
    print("- Automated layout adjustments in CAD workflows")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main()
    sys.exit(0)
