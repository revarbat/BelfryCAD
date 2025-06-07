"""
Usage examples for CadScene.rotateItemsByTags() method

This demonstrates practical examples of how to use the rotateItemsByTags method
for common CAD operations like rotating components, adjusting orientations, and
performing design iterations while preserving certain reference items.
"""

from PySide6.QtWidgets import QApplication
import sys
from BelfryCAD.gui.cad_scene import CadScene

def mechanical_part_rotation_example():
    """Example: Rotate mechanical parts for different orientations"""

    scene = CadScene()

    # Create a mechanical component with multiple orientations
    # Main housing in horizontal orientation
    scene.addRect(0, 0, 150, 80, tags=["housing", "main", "rotatable"])
    scene.addEllipse(20, 20, 20, 20, tags=["housing", "bearing", "rotatable"])
    scene.addEllipse(110, 20, 20, 20, tags=["housing", "bearing", "rotatable"])
    scene.addLine(40, 40, 110, 40, tags=["housing", "shaft", "rotatable"])

    # Mounting brackets that should rotate with the housing
    scene.addRect(10, -20, 20, 20, tags=["housing", "bracket", "rotatable"])
    scene.addRect(120, -20, 20, 20, tags=["housing", "bracket", "rotatable"])

    # Create reference coordinate system (should not rotate)
    scene.addLine(-50, 0, 200, 0, tags=["reference", "x_axis", "fixed"])
    scene.addLine(0, -50, 0, 130, tags=["reference", "y_axis", "fixed"])
    scene.addText("X", tags=["reference", "label", "fixed"])
    scene.addText("Y", tags=["reference", "label", "fixed"])

    # Create assembly bolts (separate rotatable group)
    scene.addEllipse(15, 85, 8, 8, tags=["fastener", "bolt", "rotatable"])
    scene.addEllipse(45, 85, 8, 8, tags=["fastener", "bolt", "rotatable"])
    scene.addEllipse(105, 85, 8, 8, tags=["fastener", "bolt", "rotatable"])
    scene.addEllipse(135, 85, 8, 8, tags=["fastener", "bolt", "rotatable"])

    print(f"Created mechanical part: {len(scene.scene.items())} items")

    # Get item counts
    housing_items = scene.getItemsByTags(["housing", "rotatable"])
    fastener_items = scene.getItemsByTags(["fastener", "rotatable"])
    reference_items = scene.getItemsByTags(["reference"])

    print(f"Housing components: {len(housing_items)}")
    print(f"Fasteners: {len(fastener_items)}")
    print(f"Reference items: {len(reference_items)}")

    print("\n1. Rotating housing assembly to vertical orientation (90°):")
    rotated = scene.rotateItemsByTags(["housing", "rotatable"], 90.0, 75.0, 40.0)
    print(f"   Rotated {rotated} housing components around center (75, 40)")

    print("\n2. Adjusting fastener positions (rotate 45° around assembly center):")
    rotated = scene.rotateItemsByTags(["fastener", "rotatable"], 45.0, 75.0, 85.0)
    print(f"   Rotated {rotated} fasteners")

    print("\nResult: Housing rotated to vertical, fasteners adjusted, reference axes unchanged")


def assembly_orientation_example():
    """Example: Rotate different sub-assemblies to different orientations"""

    scene = CadScene()

    # Create a multi-part assembly
    # Motor assembly (horizontal)
    scene.addRect(0, 0, 100, 60, tags=["assembly", "motor", "rotatable"])
    scene.addEllipse(80, 25, 30, 30, tags=["assembly", "motor_shaft", "rotatable"])
    scene.addRect(10, 10, 80, 15, tags=["assembly", "motor_coils", "rotatable"])
    scene.addRect(10, 35, 80, 15, tags=["assembly", "motor_coils", "rotatable"])

    # Gear box (should rotate to mesh with motor)
    scene.addRect(120, 10, 60, 40, tags=["assembly", "gearbox", "rotatable"])
    scene.addEllipse(135, 20, 15, 15, tags=["assembly", "gear1", "rotatable"])
    scene.addEllipse(155, 20, 15, 15, tags=["assembly", "gear2", "rotatable"])
    scene.addEllipse(165, 35, 10, 10, tags=["assembly", "output_shaft", "rotatable"])

    # Conveyor belt system
    scene.addRect(200, 0, 200, 20, tags=["assembly", "conveyor", "rotatable"])
    scene.addEllipse(210, 10, 20, 20, tags=["assembly", "roller1", "rotatable"])
    scene.addEllipse(380, 10, 20, 20, tags=["assembly", "roller2", "rotatable"])

    # Control panel (should rotate independently)
    scene.addRect(50, 80, 100, 60, tags=["assembly", "control", "rotatable"])
    scene.addRect(60, 90, 30, 20, tags=["assembly", "display", "rotatable"])
    scene.addEllipse(100, 95, 8, 8, tags=["assembly", "button1", "rotatable"])
    scene.addEllipse(115, 95, 8, 8, tags=["assembly", "button2", "rotatable"])
    scene.addEllipse(130, 95, 8, 8, tags=["assembly", "emergency", "rotatable"])

    print(f"Created assembly: {len(scene.scene.items())} items")

    # Get component counts
    motor_items = scene.getItemsByTags(["assembly", "motor"])
    gearbox_items = scene.getItemsByTags(["assembly", "gearbox"])
    conveyor_items = scene.getItemsByTags(["assembly", "conveyor"])
    control_items = scene.getItemsByTags(["assembly", "control"])

    print(f"Motor components: {len(motor_items)}")
    print(f"Gearbox components: {len(gearbox_items)}")
    print(f"Conveyor components: {len(conveyor_items)}")
    print(f"Control components: {len(control_items)}")

    print("\n1. Tilting motor assembly by 15° for better alignment:")
    rotated = scene.rotateItemsByTags(["assembly", "motor"], 15.0, 50.0, 30.0)
    print(f"   Rotated {rotated} motor components")

    print("\n2. Adjusting gearbox orientation to match motor angle:")
    rotated = scene.rotateItemsByTags(["assembly", "gearbox"], 15.0, 150.0, 30.0)
    print(f"   Rotated {rotated} gearbox components")

    print("\n3. Rotating conveyor system to 5° incline:")
    rotated = scene.rotateItemsByTags(["assembly", "conveyor"], 5.0, 300.0, 10.0)
    print(f"   Rotated {rotated} conveyor components")

    print("\n4. Rotating control panel to face operator (30° turn):")
    rotated = scene.rotateItemsByTags(["assembly", "control"], 30.0, 100.0, 110.0)
    print(f"   Rotated {rotated} control components")


def design_iteration_example():
    """Example: Rotate components for design iterations and comparisons"""

    scene = CadScene()

    # Create multiple design variations of the same component
    # Original design (0°)
    scene.addRect(0, 0, 80, 40, tags=["design", "v1", "original"])
    scene.addEllipse(10, 10, 15, 15, tags=["design", "v1", "feature"])
    scene.addEllipse(55, 10, 15, 15, tags=["design", "v1", "feature"])
    scene.addLine(25, 20, 55, 20, tags=["design", "v1", "connection"])

    # Design variation 2 (will be rotated 45°)
    scene.addRect(100, 0, 80, 40, tags=["design", "v2", "rotatable"])
    scene.addEllipse(110, 10, 15, 15, tags=["design", "v2", "feature", "rotatable"])
    scene.addEllipse(155, 10, 15, 15, tags=["design", "v2", "feature", "rotatable"])
    scene.addLine(125, 20, 155, 20, tags=["design", "v2", "connection", "rotatable"])

    # Design variation 3 (will be rotated 90°)
    scene.addRect(200, 0, 80, 40, tags=["design", "v3", "rotatable"])
    scene.addEllipse(210, 10, 15, 15, tags=["design", "v3", "feature", "rotatable"])
    scene.addEllipse(255, 10, 15, 15, tags=["design", "v3", "feature", "rotatable"])
    scene.addLine(225, 20, 255, 20, tags=["design", "v3", "connection", "rotatable"])

    # Design variation 4 (will be rotated 135°)
    scene.addRect(300, 0, 80, 40, tags=["design", "v4", "rotatable"])
    scene.addEllipse(310, 10, 15, 15, tags=["design", "v4", "feature", "rotatable"])
    scene.addEllipse(355, 10, 15, 15, tags=["design", "v4", "feature", "rotatable"])
    scene.addLine(325, 20, 355, 20, tags=["design", "v4", "connection", "rotatable"])

    # Add comparison grid and labels
    scene.addLine(-20, -20, 400, -20, tags=["reference", "grid"])
    scene.addLine(-20, 60, 400, 60, tags=["reference", "grid"])
    scene.addText("Original", tags=["reference", "label"])
    scene.addText("45°", tags=["reference", "label"])
    scene.addText("90°", tags=["reference", "label"])
    scene.addText("135°", tags=["reference", "label"])

    print(f"Created design comparison: {len(scene.scene.items())} items")

    print("\n1. Rotating design v2 to 45° orientation:")
    rotated = scene.rotateItemsByTags(["design", "v2", "rotatable"], 45.0, 140.0, 20.0)
    print(f"   Rotated {rotated} v2 components")

    print("\n2. Rotating design v3 to 90° orientation:")
    rotated = scene.rotateItemsByTags(["design", "v3", "rotatable"], 90.0, 240.0, 20.0)
    print(f"   Rotated {rotated} v3 components")

    print("\n3. Rotating design v4 to 135° orientation:")
    rotated = scene.rotateItemsByTags(["design", "v4", "rotatable"], 135.0, 340.0, 20.0)
    print(f"   Rotated {rotated} v4 components")

    print("\nResult: Four design variations at different orientations for comparison")


def precision_rotation_example():
    """Example: Precise rotation for manufacturing and alignment"""

    scene = CadScene()

    # Create precision components that need exact angular positioning
    # Gear teeth (need precise angular spacing)
    center_x, center_y = 150.0, 150.0
    radius = 80.0

    # Create 12 gear teeth (30° apart)
    for i in range(12):
        angle_deg = i * 30.0
        # Create a tooth shape
        x = center_x + radius * 0.8
        y = center_y
        scene.addRect(x-5, y-10, 10, 20, tags=["gear", "tooth", f"tooth_{i}"])
        scene.addEllipse(x-2, y-2, 4, 4, tags=["gear", "tooth", f"tooth_{i}"])

    # Add gear center
    scene.addEllipse(center_x-10, center_y-10, 20, 20, tags=["gear", "center", "fixed"])

    # Create alignment marks
    scene.addLine(center_x, center_y-120, center_x, center_y+120, tags=["reference", "vertical"])
    scene.addLine(center_x-120, center_y, center_x+120, center_y, tags=["reference", "horizontal"])

    print(f"Created precision gear: {len(scene.scene.items())} items")

    print("\n1. Positioning each tooth at precise angles:")
    for i in range(12):
        angle = i * 30.0  # 30 degrees apart
        rotated = scene.rotateItemsByTags(["gear", f"tooth_{i}"], angle, center_x, center_y)
        print(f"   Tooth {i}: rotated to {angle}° ({rotated} items)")

    print("\n2. Fine adjustment - rotate entire gear assembly by 15°:")
    rotated = scene.rotateItemsByTags(["gear", "tooth"], 15.0, center_x, center_y)
    print(f"   Rotated {rotated} gear teeth for final positioning")

    print("\nResult: Precision gear with 12 teeth at exact 30° intervals")


def architectural_rotation_example():
    """Example: Rotate architectural elements for different building orientations"""

    scene = CadScene()

    # Create a building layout with rotatable elements
    # Main building structure
    scene.addRect(0, 0, 200, 150, tags=["building", "main", "rotatable"])
    scene.addRect(20, 20, 50, 40, tags=["building", "room1", "rotatable"])
    scene.addRect(80, 20, 50, 40, tags=["building", "room2", "rotatable"])
    scene.addRect(140, 20, 50, 40, tags=["building", "room3", "rotatable"])
    scene.addRect(20, 80, 160, 50, tags=["building", "hall", "rotatable"])

    # Windows and doors
    scene.addRect(25, 0, 15, 5, tags=["building", "door", "rotatable"])
    scene.addRect(30, 20, 10, 3, tags=["building", "window", "rotatable"])
    scene.addRect(90, 20, 10, 3, tags=["building", "window", "rotatable"])
    scene.addRect(150, 20, 10, 3, tags=["building", "window", "rotatable"])

    # Landscape elements (should rotate with building)
    scene.addEllipse(-20, -20, 30, 30, tags=["landscape", "tree", "rotatable"])
    scene.addEllipse(210, -20, 30, 30, tags=["landscape", "tree", "rotatable"])
    scene.addEllipse(-20, 160, 30, 30, tags=["landscape", "tree", "rotatable"])
    scene.addEllipse(210, 160, 30, 30, tags=["landscape", "tree", "rotatable"])

    # Site boundaries (should not rotate)
    scene.addRect(-50, -50, 300, 250, tags=["site", "boundary", "fixed"])
    scene.addLine(-50, 0, 250, 0, tags=["site", "property_line", "fixed"])
    scene.addText("Property Line", tags=["site", "label", "fixed"])

    print(f"Created architectural layout: {len(scene.scene.items())} items")

    # Get item counts
    building_items = scene.getItemsByTags(["building", "rotatable"])
    landscape_items = scene.getItemsByTags(["landscape", "rotatable"])
    site_items = scene.getItemsByTags(["site"])

    print(f"Building components: {len(building_items)}")
    print(f"Landscape elements: {len(landscape_items)}")
    print(f"Site elements: {len(site_items)}")

    print("\n1. Rotating building to face south (30° clockwise):")
    building_center_x, building_center_y = 100.0, 75.0
    rotated = scene.rotateItemsByTags(["building", "rotatable"], -30.0, building_center_x, building_center_y)
    print(f"   Rotated {rotated} building components")

    print("\n2. Adjusting landscape to match building orientation:")
    rotated = scene.rotateItemsByTags(["landscape", "rotatable"], -30.0, building_center_x, building_center_y)
    print(f"   Rotated {rotated} landscape elements")

    print("\nResult: Building and landscape rotated for optimal solar orientation")
    print("Site boundaries and property lines remain in original orientation")


if __name__ == "__main__":
    # Create QApplication instance (required for Qt objects)
    app = QApplication(sys.argv)

    print("CadScene.rotateItemsByTags() Usage Examples")
    print("=" * 50)

    try:
        print("\n>>> MECHANICAL PART ROTATION")
        mechanical_part_rotation_example()

        print("\n>>> ASSEMBLY ORIENTATION")
        assembly_orientation_example()

        print("\n>>> DESIGN ITERATION")
        design_iteration_example()

        print("\n>>> PRECISION ROTATION")
        precision_rotation_example()

        print("\n>>> ARCHITECTURAL ROTATION")
        architectural_rotation_example()

        print("\n" + "=" * 50)
        print("Usage examples completed successfully!")
        print("These examples demonstrate practical applications of")
        print("the rotateItemsByTags method in real CAD workflows.")
        print("=" * 50)

    except Exception as e:
        print(f"Error during examples: {e}")
        import traceback
        traceback.print_exc()
