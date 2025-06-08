#!/usr/bin/env python3
"""
Simple test to demonstrate the transformItemsByTags method.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTransform
from gui.cad_scene import CadScene


def simple_demo():
    """Simple demonstration of transformItemsByTags."""

    print("Simple transformItemsByTags Demo")
    print("=" * 40)

    # Create a CadScene instance
    cad_scene = CadScene()

    # Add some items with different tags
    line1 = cad_scene.addLine(0, 0, 100, 0, tags=["movable"])
    rect1 = cad_scene.addRect(50, 50, 100, 50, tags=["movable"])
    ellipse1 = cad_scene.addEllipse(200, 200, 80, 60, tags=["fixed"])

    print(f"\nCreated 3 items:")
    print(f"  Line1: tags=['movable']")
    print(f"  Rect1: tags=['movable']")
    print(f"  Ellipse1: tags=['fixed']")

    print(f"\nInitial transforms:")
    print(f"  Line1: {line1.transform()}")
    print(f"  Rect1: {rect1.transform()}")
    print(f"  Ellipse1: {ellipse1.transform()}")

    # Create a transformation matrix: rotate 90° and scale 200%
    transform = QTransform()
    transform.rotate(90)
    transform.scale(2.0, 2.0)

    print(f"\nApplying transformation to items with 'movable' tag:")
    print(f"  Transform: rotate 90°, scale 200%")

    # Apply transformation
    count = cad_scene.transformItemsByTags(["movable"], transform)
    print(f"  Items transformed: {count}")

    print(f"\nFinal transforms:")
    print(f"  Line1: {line1.transform()}")
    print(f"  Rect1: {rect1.transform()}")
    print(f"  Ellipse1: {ellipse1.transform()} (should be unchanged)")

    print(f"\nResult: Only items with 'movable' tag were transformed!")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        simple_demo()
        print("\nDemo completed successfully!")

    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    sys.exit(0)
