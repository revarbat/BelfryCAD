"""
Usage examples for CadScene.transformItemsByTags() method

This demonstrates practical examples of how to use the transformItemsByTags method
to apply QTransform transformation matrices to graphics items selected by tags.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTransform
import sys
from BelfryCAD.gui.cad_scene import CadScene


def basic_rotation_example():
    """Example: Basic rotation using QTransform"""

    scene = CadScene()

    # Create some geometric shapes
    scene.addLine(0, 0, 100, 0, tags=["geometry", "rotatable"])
    scene.addRect(50, 50, 100, 50, tags=["geometry", "rotatable"])
    scene.addEllipse(200, 200, 80, 60, tags=["geometry", "fixed"])

    print(f"Created shapes: {len(scene.scene.items())} items")

    # Create rotation transform (45 degrees)
    rotation_transform = QTransform()
    rotation_transform.rotate(45)

    # Apply to rotatable items
    rotated = scene.transformItemsByTags(["geometry", "rotatable"],
                                         rotation_transform)
    print(f"Rotated {rotated} items by 45 degrees")


def scaling_example():
    """Example: Scaling using QTransform"""

    scene = CadScene()

    # Create components
    scene.addRect(0, 0, 100, 60, tags=["component", "scalable"])
    scene.addLine(30, 30, 70, 30, tags=["component", "scalable"])
    scene.addText("Label", tags=["component", "fixed"])

    # Create scaling transform (150%)
    scale_transform = QTransform()
    scale_transform.scale(1.5, 1.5)

    # Apply to scalable components
    scaled = scene.transformItemsByTags(["component", "scalable"],
                                        scale_transform)
    print(f"Scaled {scaled} components to 150%")


def complex_transformation_example():
    """Example: Complex transformation combining multiple operations"""

    scene = CadScene()

    # Create assembly parts
    scene.addRect(100, 100, 80, 40, tags=["assembly", "part"])
    scene.addEllipse(110, 110, 15, 15, tags=["assembly", "part"])
    scene.addLine(100, 120, 180, 120, tags=["assembly", "part"])

    # Create complex transform: translate, rotate, scale
    complex_transform = QTransform()
    complex_transform.translate(50, 25)  # Move first
    complex_transform.rotate(30)         # Then rotate
    complex_transform.scale(0.8, 1.2)    # Then scale differently in X and Y

    # Apply to assembly parts
    transformed = scene.transformItemsByTags(["assembly", "part"],
                                             complex_transform)
    print(f"Applied complex transformation to {transformed} assembly parts")


def main():
    """Demo all the examples"""
    print("CadScene.transformItemsByTags() Usage Examples")
    print("=" * 50)

    print("\n1. Basic Rotation")
    print("-" * 30)
    basic_rotation_example()

    print("\n2. Scaling")
    print("-" * 30)
    scaling_example()

    print("\n3. Complex Transformation")
    print("-" * 30)
    complex_transformation_example()

    print("\n" + "=" * 50)
    print("Key Benefits of transformItemsByTags:")
    print("- Apply QTransform matrices to tagged item groups")
    print("- Combine rotation, scaling, translation, and shearing")
    print("- Precise mathematical transformations")
    print("- Maintain tag-based organization")
    print("- Efficient batch transformation operations")
    print("=" * 50)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main()
    sys.exit(0)
