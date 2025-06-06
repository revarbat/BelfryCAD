#!/usr/bin/env python3
"""
Test script to verify the Y-axis coordinate system transformation fix.
This tests that coordinates are properly flipped from CAD convention (Y up) to Qt convention (Y down).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.drawing_manager import DrawingManager, DrawingContext
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

def test_coordinate_transformation():
    """Test the coordinate transformation functions"""
    print("Testing Y-axis coordinate system transformation...")

    # Create Qt application and context
    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    view = QGraphicsView(scene)

    # Create graphics context with test values
    context = DrawingContext(scene)
    context.dpi = 100.0  # 100 DPI for easy calculations
    context.scale_factor = 1.0  # No additional scaling

    # Create drawing manager
    drawing_manager = DrawingManager(context)

    # Test coordinate pairs (CAD coordinates)
    test_coords = [
        [0.0, 0.0],      # Origin
        [1.0, 1.0],      # Positive quadrant
        [-1.0, 1.0],     # Second quadrant
        [-1.0, -1.0],    # Third quadrant
        [1.0, -1.0],     # Fourth quadrant
    ]

    print("\nTesting scale_coords (CAD -> Canvas):")
    print("DPI: 100, Scale Factor: 1.0")
    print("Expected behavior: X normal scaling, Y negative scaling")
    print("-" * 60)

    for cad_coords in test_coords:
        canvas_coords = drawing_manager.scale_coords(cad_coords)
        print(f"CAD {cad_coords} -> Canvas {canvas_coords}")

        # Verify transformation
        expected_x = cad_coords[0] * 100.0  # Normal scaling
        expected_y = -cad_coords[1] * 100.0  # Negative scaling (Y flip)

        if abs(canvas_coords[0] - expected_x) < 1e-6 and abs(canvas_coords[1] - expected_y) < 1e-6:
            print(f"  ✓ Correct: X={expected_x}, Y={expected_y}")
        else:
            print(f"  ✗ Error: Expected X={expected_x}, Y={expected_y}")

    print("\nTesting descale_coords (Canvas -> CAD):")
    print("-" * 60)

    # Test the reverse transformation
    for cad_coords in test_coords:
        canvas_coords = drawing_manager.scale_coords(cad_coords)
        recovered_coords = drawing_manager.descale_coords(canvas_coords)
        print(f"CAD {cad_coords} -> Canvas {canvas_coords} -> CAD {recovered_coords}")

        # Verify round-trip transformation
        if (abs(recovered_coords[0] - cad_coords[0]) < 1e-6 and
            abs(recovered_coords[1] - cad_coords[1]) < 1e-6):
            print(f"  ✓ Round-trip successful")
        else:
            print(f"  ✗ Round-trip error")

    print("\nTesting coordinate system behavior:")
    print("-" * 60)

    # Test specific coordinate system behavior
    # In CAD: positive Y goes up
    # In Qt: positive Y goes down
    # Our transformation should flip Y-axis

    cad_up = [0.0, 1.0]  # Point 1 unit up in CAD
    canvas_up = drawing_manager.scale_coords(cad_up)
    print(f"CAD point 1 unit UP {cad_up} -> Canvas {canvas_up}")
    print(f"  Canvas Y is {canvas_up[1]} (should be negative for 'up' in CAD)")

    cad_down = [0.0, -1.0]  # Point 1 unit down in CAD
    canvas_down = drawing_manager.scale_coords(cad_down)
    print(f"CAD point 1 unit DOWN {cad_down} -> Canvas {canvas_down}")
    print(f"  Canvas Y is {canvas_down[1]} (should be positive for 'down' in CAD)")

    print("\nY-axis flip verification:")
    print(f"  CAD UP (Y=+1) maps to Canvas Y={canvas_up[1]} (negative = correct)")
    print(f"  CAD DOWN (Y=-1) maps to Canvas Y={canvas_down[1]} (positive = correct)")

    if canvas_up[1] < 0 and canvas_down[1] > 0:
        print("  ✓ Y-axis flip is working correctly!")
    else:
        print("  ✗ Y-axis flip is NOT working correctly!")

    print("\nCoordinate transformation test completed.")

    app.quit()

if __name__ == "__main__":
    test_coordinate_transformation()
