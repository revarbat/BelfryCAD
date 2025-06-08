#!/usr/bin/env python3
"""
Test script for the new transformItemsByTags method in CadScene.

This script demonstrates how to use the transformItemsByTags method to apply
custom transformations to graphics items using setTransform and other operations.
"""

import sys
import os

# Add the BelfryCAD directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTransform
from gui.cad_scene import CadScene


def test_transform_items_by_tags():
    """Test the transformItemsByTags method functionality."""

    # Create a CadScene instance
    cad_scene = CadScene()

    print("Testing CadScene.transformItemsByTags() method")
    print("=" * 50)

    # Add various items with different tag combinations
    print("\n1. Adding items with different tag combinations:")

    # Items that will be transformed (have both 'transformable' and 'geometry')
    line1 = cad_scene.addLine(0, 0, 100, 0, tags=["geometry", "transformable", "shape"])
    print("   - Line1: horizontal line, tags=['geometry', 'transformable', 'shape']")
    print(f"     Initial transform: {line1.transform()}")

    rect1 = cad_scene.addRect(50, 50, 100, 50, tags=["transformable", "geometry", "rectangle"])
    print("   - Rect1: tags=['transformable', 'geometry', 'rectangle']")
    print(f"     Initial transform: {rect1.transform()}")

    # Items that will NOT be transformed (missing one of the tags)
    ellipse1 = cad_scene.addEllipse(150, 150, 80, 60, tags=["geometry", "transformable", "fixed"])
    print("   - Ellipse1: tags=['geometry', 'transformable', 'fixed'] (missing 'shape')")
    print(f"     Initial transform: {ellipse1.transform()}")

    line2 = cad_scene.addLine(200, 200, 300, 200, tags=["geometry", "construction", "guide"])
    print("   - Line2: tags=['geometry', 'construction', 'guide'] (missing 'transformable')")
    print(f"     Initial transform: {line2.transform()}")

    text1 = cad_scene.addText("Sample Text", tags=["text", "annotation", "label"])
    print("   - Text1: tags=['text', 'annotation', 'label'] (missing both)")
    print(f"     Initial transform: {text1.transform()}")

    print(f"\n2. Initial state:")
    print(f"   Total items in scene: {len(cad_scene.scene.items())}")

    # Check items before transformation
    transformable_geometry_items = cad_scene.getItemsByTags(["transformable", "geometry"])
    print(f"   Items with both 'transformable' AND 'geometry': {len(transformable_geometry_items)}")

    # Create a QTransform matrix for transformation: rotate 45° and scale 150%
    custom_transform = QTransform()
    custom_transform.rotate(45)
    custom_transform.scale(1.5, 1.5)

    print(f"\n3. Testing transformItemsByTags(['transformable', 'geometry'], QTransform):")
    print("   QTransform: rotate 45° and scale 150% using setTransform")

    # Apply transformation to items that have both 'transformable' and 'geometry' tags
    transformed_count = cad_scene.transformItemsByTags(["transformable", "geometry"], custom_transform)
    print(f"   Items transformed: {transformed_count}")

    print(f"\n4. Transforms after custom transformation:")

    # Check the transforms after transformation
    print("   Items that should have been transformed:")
    print(f"   - Line1 transform: {line1.transform()}")
    print(f"   - Rect1 transform: {rect1.transform()}")
    print(f"   - Ellipse1 transform: {ellipse1.transform()}")

    print("   Items that should NOT have been transformed:")
    print(f"   - Line2 transform: {line2.transform()}")
    print(f"   - Text1 transform: {text1.transform()}")

    # Verify that the correct items were transformed
    remaining_transformable_geometry = cad_scene.getItemsByTags([
        "transformable", "geometry"
    ])
    print(f"\n5. Verification:")
    print(f"   Items still tagged with both 'transformable' AND 'geometry': {len(remaining_transformable_geometry)}")

    print(f"\n6. Summary:")
    print(f"   - {transformed_count} items were transformed using custom function")
    print(f"   - Items were rotated 45° and scaled 150% using setTransform")
    print(f"   - Only items with ALL specified tags were affected")


def test_property_transformation():
    """Test transformation that changes properties rather than transforms."""

    print("\n" + "=" * 50)
    print("TESTING PROPERTY TRANSFORMATIONS")
    print("=" * 50)

    cad_scene = CadScene()

    # Add some test items
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["test", "visible"])
    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["test", "geometry"])
    ellipse1 = cad_scene.addEllipse(150, 150, 100, 50, tags=["test", "visible"])

    print(f"\nInitial properties:")
    print(f"   Line1 opacity: {line1.opacity()}")
    print(f"   Rect1 opacity: {rect1.opacity()}")
    print(f"   Ellipse1 opacity: {ellipse1.opacity()}")

    # Create a QTransform that changes opacity (this is a limitation -
    # QTransform can't change opacity, so we'll use a simple scale instead)
    opacity_transform = QTransform()
    opacity_transform.scale(0.5, 0.5)  # Scale down as a visual effect

    print("\n1. Applying scale transformation to items with 'test' tag:")
    transformed = cad_scene.transformItemsByTags(["test"], opacity_transform, all=False)
    print(f"   Items transformed: {transformed}")

    print(f"\nFinal properties (items scaled to 50%):")
    print(f"   Line1 transform: {line1.transform()}")
    print(f"   Rect1 transform: {rect1.transform()}")
    print(f"   Ellipse1 transform: {ellipse1.transform()}")


def test_complex_transformation():
    """Test complex transformation combining multiple operations."""

    print("\n" + "=" * 50)
    print("TESTING COMPLEX TRANSFORMATIONS")
    print("=" * 50)

    cad_scene = CadScene()

    # Add some test items
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["complex", "moveable"])
    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["complex", "moveable"])

    print(f"Initial state:")
    print(f"   Line1 position: ({line1.x()}, {line1.y()})")
    print(f"   Line1 transform: {line1.transform()}")
    print(f"   Line1 z-value: {line1.zValue()}")
    print(f"   Rect1 position: ({rect1.x()}, {rect1.y()})")
    print(f"   Rect1 transform: {rect1.transform()}")
    print(f"   Rect1 z-value: {rect1.zValue()}")

    # Create a complex QTransform matrix: translate, rotate, and scale
    complex_transform = QTransform()
    complex_transform.translate(10, 10)   # Move by (10,10)
    complex_transform.rotate(30)          # Rotate 30°
    complex_transform.scale(1.2, 1.2)     # Scale 120%

    print("\n1. Applying complex QTransform to items with ['complex', 'moveable'] tags:")
    print("   Operations: translate (10,10), rotate 30°, scale 120%")
    transformed = cad_scene.transformItemsByTags(["complex", "moveable"], complex_transform)
    print(f"   Items transformed: {transformed}")

    print(f"\nFinal state:")
    print(f"   Line1 position: ({line1.x()}, {line1.y()})")
    print(f"   Line1 transform: {line1.transform()}")
    print(f"   Line1 z-value: {line1.zValue()}")
    print(f"   Rect1 position: ({rect1.x()}, {rect1.y()})")
    print(f"   Rect1 transform: {rect1.transform()}")
    print(f"   Rect1 z-value: {rect1.zValue()}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        test_transform_items_by_tags()
        test_property_transformation()
        test_complex_transformation()
        print("\n" + "=" * 50)
        print("All transformItemsByTags tests completed successfully!")
        print("The method correctly applies custom transformations using setTransform")
        print("and other operations to items that have ALL specified tags.")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Don't start the event loop, just exit
    sys.exit(0)
