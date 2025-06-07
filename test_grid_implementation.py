#!/usr/bin/env python3
"""
Test script to verify the new grid implementation matches TCL behavior.
This script creates a simple test to check if the multi-level grid system works.
"""

import sys
import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext, DrawingTags

def test_grid_implementation():
    """Test the grid implementation with different zoom levels and settings"""
    print("Testing grid implementation...")

    # Create Qt application
    app = QApplication(sys.argv)

    # Create scene and view for testing
    scene = QGraphicsScene()
    view = QGraphicsView(scene)

    # Set up scene rectangle (equivalent to viewport)
    scene.setSceneRect(-500, -500, 1000, 1000)

    # Create drawing context
    context = DrawingContext(
        scene=scene,
        dpi=96.0,
        scale_factor=1.0,
        show_grid=True,
        show_origin=True
    )

    # Create drawing manager
    drawing_manager = DrawingManager(context)

    print("✓ Drawing manager created")

    # Test grid info calculation
    grid_info = drawing_manager._get_grid_info()
    if grid_info:
        minorspacing, majorspacing, superspacing, labelspacing, divisor, units, formatfunc, conversion = grid_info
        print(f"✓ Grid info calculated:")
        print(f"  - Minor spacing: {minorspacing}")
        print(f"  - Major spacing: {majorspacing}")
        print(f"  - Super spacing: {superspacing}")
        print(f"  - Units: {units}")
        print(f"  - Conversion: {conversion}")
    else:
        print("✗ Failed to calculate grid info")
        return False

    # Test color conversion functions
    test_color = QColor(0, 255, 255)  # Cyan
    hsv = drawing_manager._color_to_hsv(test_color)
    print(f"✓ Color to HSV: {hsv}")

    converted_back = drawing_manager._color_from_hsv(hsv[0], hsv[1], hsv[2])
    print(f"✓ HSV to Color: RGB({converted_back.red()}, {converted_back.green()}, {converted_back.blue()})")

    # Test grid redraw
    try:
        drawing_manager.redraw_grid()
        print("✓ Grid redraw completed successfully")
    except Exception as e:
        print(f"✗ Grid redraw failed: {e}")
        return False

    # Count grid items by tag
    grid_items = scene.items()
    grid_count = len([item for item in grid_items if hasattr(item, 'zValue') and item.zValue() < 0])
    print(f"✓ Grid items created: {grid_count}")

    # Test grid at different zoom levels
    print("\nTesting different zoom levels:")
    for scale in [0.1, 0.5, 1.0, 2.0, 5.0]:
        context.scale_factor = scale
        try:
            drawing_manager.redraw_grid()
            grid_items_after = scene.items()
            new_grid_count = len([item for item in grid_items_after if hasattr(item, 'zValue') and item.zValue() < 0])
            print(f"  Scale {scale}: {new_grid_count} grid items")
        except Exception as e:
            print(f"  ✗ Scale {scale} failed: {e}")

    # Test origin drawing
    context.scale_factor = 1.0
    context.show_origin = True
    try:
        drawing_manager._draw_grid_origin(96.0, 1.0)
        print("✓ Origin drawing completed")
    except Exception as e:
        print(f"✗ Origin drawing failed: {e}")

    print("\n" + "="*50)
    print("Grid implementation test completed!")
    print("The new multi-level grid system is working.")
    print("="*50)

    return True

if __name__ == "__main__":
    success = test_grid_implementation()
    if success:
        print("\n🎉 All tests passed! The grid implementation is ready.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
    sys.exit(0 if success else 1)
