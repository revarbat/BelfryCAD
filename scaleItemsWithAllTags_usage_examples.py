"""
Usage examples for CadScene.scaleItemsByTags() method

This demonstrates practical examples of how to use the scaleItemsByTags method
for common CAD operations like scaling components, resizing assemblies, and
adjusting design elements while preserving certain reference items.
"""

from PySide6.QtWidgets import QApplication
import sys
from BelfryCAD.gui.cad_scene import CadScene

def component_scaling_example():
    """Example: Scale entire components while preserving references"""

    scene = CadScene()

    # Create a mechanical component with multiple parts
    # Main housing
    scene.addRect(0, 0, 100, 60, tags=["component", "housing", "scalable"])
    scene.addEllipse(10, 10, 20, 20, tags=["component", "bearing", "scalable"])
    scene.addEllipse(70, 10, 20, 20, tags=["component", "bearing", "scalable"])
    scene.addLine(30, 30, 70, 30, tags=["component", "shaft", "scalable"])

    # Create reference dimensions that should not scale
    scene.addLine(0, -20, 100, -20, tags=["dimension", "reference", "fixed"])
    scene.addText("100mm", tags=["dimension", "label", "fixed"])
    scene.addLine(-20, 0, -20, 60, tags=["dimension", "reference", "fixed"])
    scene.addText("60mm", tags=["dimension", "label", "fixed"])

    # Create mounting holes (separate scalable group)
    scene.addEllipse(15, 45, 10, 10, tags=["mounting", "hole", "scalable"])
    scene.addEllipse(75, 45, 10, 10, tags=["mounting", "hole", "scalable"])

    print(f"Created mechanical component: {len(scene.scene.items())} items")

    # Get item counts
    component_items = scene.getItemsByTags(["component", "scalable"])
    mounting_items = scene.getItemsByTags(["mounting", "scalable"])
    reference_items = scene.getItemsByTags(["dimension"])

    print(f"Component parts: {len(component_items)}")
    print(f"Mounting holes: {len(mounting_items)}")
    print(f"Reference dimensions: {len(reference_items)}")

    print("\n1. Scaling main component by 120%:")
    scaled = scene.scaleItemsByTags(["component", "scalable"], 1.2, 1.2)
    print(f"   Scaled {scaled} component parts")

    print("\n2. Scaling mounting holes independently (80%):")
    scaled = scene.scaleItemsByTags(["mounting", "scalable"], 0.8, 0.8)
    print(f"   Scaled {scaled} mounting holes")

    print("\nResult: Component scaled to 120%, holes to 80%, dimensions unchanged")


def assembly_scaling_example():
    """Example: Scale different parts of an assembly independently"""

    scene = CadScene()

    # Create an assembly with multiple sub-components
    # Base plate
    scene.addRect(0, 0, 200, 100, tags=["assembly", "base", "plate"])
    scene.addEllipse(25, 25, 20, 20, tags=["assembly", "base", "hole"])
    scene.addEllipse(175, 25, 20, 20, tags=["assembly", "base", "hole"])
    scene.addEllipse(25, 75, 20, 20, tags=["assembly", "base", "hole"])
    scene.addEllipse(175, 75, 20, 20, tags=["assembly", "base", "hole"])

    # Motor mount
    scene.addRect(50, 120, 100, 80, tags=["assembly", "motor", "mount"])
    scene.addEllipse(100, 160, 30, 30, tags=["assembly", "motor", "shaft"])

    # Control box
    scene.addRect(220, 50, 60, 100, tags=["assembly", "control", "box"])
    scene.addRect(230, 60, 40, 20, tags=["assembly", "control", "display"])
    scene.addEllipse(235, 90, 10, 10, tags=["assembly", "control", "button"])
    scene.addEllipse(255, 90, 10, 10, tags=["assembly", "control", "button"])
    scene.addEllipse(245, 110, 10, 10, tags=["assembly", "control", "button"])

    print(f"Created assembly: {len(scene.scene.items())} items")

    # Get component counts
    base_items = scene.getItemsByTags(["assembly", "base"])
    motor_items = scene.getItemsByTags(["assembly", "motor"])
    control_items = scene.getItemsByTags(["assembly", "control"])

    print(f"Base components: {len(base_items)}")
    print(f"Motor components: {len(motor_items)}")
    print(f"Control components: {len(control_items)}")

    print("\n1. Scaling base plate to 110% (slight enlargement):")
    scaled = scene.scaleItemsByTags(["assembly", "base"], 1.1, 1.1)
    print(f"   Scaled {scaled} base components")

    print("\n2. Scaling motor mount to 90% (size reduction):")
    scaled = scene.scaleItemsByTags(["assembly", "motor"], 0.9, 0.9)
    print(f"   Scaled {scaled} motor components")

    print("\n3. Scaling control box vertically only (stretch to 150% height):")
    scaled = scene.scaleItemsByTags(["assembly", "control"], 1.0, 1.5)
    print(f"   Scaled {scaled} control components")

    print("Result: Independent scaling of assembly components")


def design_iteration_example():
    """Example: Design iteration with proportional scaling"""

    scene = CadScene()

    # Create a design layout with different elements
    # Main design elements
    scene.addRect(50, 50, 100, 100, tags=["design", "primary", "shape"])
    scene.addEllipse(75, 75, 50, 50, tags=["design", "primary", "detail"])
    scene.addLine(50, 100, 150, 100, tags=["design", "primary", "centerline"])

    # Secondary design elements
    scene.addRect(200, 50, 60, 60, tags=["design", "secondary", "shape"])
    scene.addEllipse(220, 70, 20, 20, tags=["design", "secondary", "detail"])

    # Annotation elements (should not scale)
    scene.addText("Version 1.0", tags=["annotation", "version", "fixed"])
    scene.addText("Main Design", tags=["annotation", "title", "fixed"])
    scene.addLine(0, 200, 300, 200, tags=["annotation", "baseline", "fixed"])

    # Construction elements for scaling reference
    scene.addRect(25, 25, 150, 150, tags=["construction", "boundary", "reference"])

    print(f"Created design layout: {len(scene.scene.items())} items")

    # Get element counts
    primary_items = scene.getItemsByTags(["design", "primary"])
    secondary_items = scene.getItemsByTags(["design", "secondary"])
    annotation_items = scene.getItemsByTags(["annotation"])
    construction_items = scene.getItemsByTags(["construction"])

    print(f"Primary design elements: {len(primary_items)}")
    print(f"Secondary design elements: {len(secondary_items)}")
    print(f"Annotations: {len(annotation_items)}")
    print(f"Construction references: {len(construction_items)}")

    print("\n1. Iteration 1: Scale primary elements to 125%:")
    scaled = scene.scaleItemsByTags(["design", "primary"], 1.25, 1.25)
    print(f"   Scaled {scaled} primary elements")

    print("\n2. Iteration 2: Scale secondary elements to 75%:")
    scaled = scene.scaleItemsByTags(["design", "secondary"], 0.75, 0.75)
    print(f"   Scaled {scaled} secondary elements")

    print("\n3. Scale construction boundary to match (125%):")
    scaled = scene.scaleItemsByTags(["construction", "reference"], 1.25, 1.25)
    print(f"   Scaled {scaled} construction elements")

    print("Result: Design iteration with preserved annotations")


def precision_scaling_example():
    """Example: Precision scaling for manufacturing tolerances"""

    scene = CadScene()

    # Create precision parts with tight tolerances
    # Critical dimension parts
    scene.addRect(0, 0, 50.0, 25.0, tags=["part", "critical", "tolerance"])
    scene.addEllipse(12.5, 12.5, 5.0, 5.0, tags=["part", "critical", "hole"])
    scene.addEllipse(37.5, 12.5, 5.0, 5.0, tags=["part", "critical", "hole"])

    # Standard dimension parts
    scene.addRect(70, 0, 40.0, 20.0, tags=["part", "standard", "tolerance"])
    scene.addEllipse(85, 10, 8.0, 8.0, tags=["part", "standard", "hole"])

    # Reference gauges (must remain exact)
    scene.addRect(0, 40, 25.0, 25.0, tags=["gauge", "reference", "exact"])
    scene.addText("25.000mm", tags=["gauge", "dimension", "exact"])

    print(f"Created precision parts: {len(scene.scene.items())} items")

    # Get part counts
    critical_items = scene.getItemsByTags(["part", "critical"])
    standard_items = scene.getItemsByTags(["part", "standard"])
    gauge_items = scene.getItemsByTags(["gauge"])

    print(f"Critical tolerance parts: {len(critical_items)}")
    print(f"Standard tolerance parts: {len(standard_items)}")
    print(f"Reference gauges: {len(gauge_items)}")

    print("\n1. Adjust critical parts for tight tolerance (+0.1%):")
    scaled = scene.scaleItemsByTags(["part", "critical"], 1.001, 1.001)
    print(f"   Scaled {scaled} critical parts by +0.1%")

    print("\n2. Adjust standard parts for manufacturing (+0.5%):")
    scaled = scene.scaleItemsByTags(["part", "standard"], 1.005, 1.005)
    print(f"   Scaled {scaled} standard parts by +0.5%")

    print("\n3. Reference gauges remain exact (no scaling)")
    print("   Gauges maintain original dimensions for verification")

    print("Result: Precision tolerance adjustments applied")


def main():
    """Demo all the examples"""
    print("CadScene.scaleItemsByTags() Usage Examples")
    print("=" * 50)

    print("\n1. Component Scaling")
    print("-" * 30)
    component_scaling_example()

    print("\n2. Assembly Scaling")
    print("-" * 30)
    assembly_scaling_example()

    print("\n3. Design Iteration")
    print("-" * 30)
    design_iteration_example()

    print("\n4. Precision Scaling")
    print("-" * 30)
    precision_scaling_example()

    print("\n" + "=" * 50)
    print("Key Benefits of scaleItemsByTags:")
    print("- Scale entire components while preserving references")
    print("- Independent scaling of assembly parts")
    print("- Non-uniform scaling for design adjustments")
    print("- Precision tolerance adjustments")
    print("- Maintain relationships between related elements")
    print("- Selective scaling based on tag combinations")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main()
    sys.exit(0)
