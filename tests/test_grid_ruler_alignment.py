#!/usr/bin/env python3
"""
Test script to verify that grid lines align with ruler tick marks.
This script tests the grid-ruler alignment issue fix.
"""

import sys
import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def test_grid_ruler_alignment():
    """Test that grid lines align with ruler tick marks"""
    print("Testing grid-ruler alignment...")

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

    # Create a test ruler widget
    ruler = RulerWidget(view, "horizontal")

    print("✓ Test components created")

    # Compare grid info from both systems
    drawing_grid_info = drawing_manager._get_grid_info()
    ruler_grid_info = ruler.get_grid_info()

    print("\nGrid info comparison:")
    print("DrawingManager grid info:", drawing_grid_info)
    print("Ruler grid info:         ", ruler_grid_info)

    # Check if they match exactly
    alignment_ok = True
    if drawing_grid_info == ruler_grid_info:
        print("✅ Grid info matches exactly - alignment should be perfect!")
    else:
        print("❌ Grid info differs - checking individual values...")
        alignment_ok = False

        labels = ["minorspacing", "majorspacing", "superspacing", "labelspacing",
                 "divisor", "units", "formatfunc", "conversion"]

        for i, label in enumerate(labels):
            drawing_val = drawing_grid_info[i]
            ruler_val = ruler_grid_info[i]
            if drawing_val == ruler_val:
                print(f"  ✓ {label}: {drawing_val}")
            else:
                print(f"  ❌ {label}: DrawingManager={drawing_val}, Ruler={ruler_val}")

    # Test grid drawing with the new aligned system
    print("\nTesting aligned grid drawing...")
    try:
        drawing_manager.redraw_grid()
        print("✓ Grid redraw completed successfully")

        # Count grid items
        grid_items = scene.items()
        grid_count = len([item for item in grid_items if hasattr(item, 'zValue') and item.zValue() < 0])
        print(f"✓ Grid items created: {grid_count}")

    except Exception as e:
        print(f"✗ Grid redraw failed: {e}")
        alignment_ok = False

    # Simulate old grid alignment test
    print("\nTesting alignment logic...")
    (minorspacing, majorspacing, superspacing, labelspacing,
     divisor, units, formatfunc, conversion) = ruler_grid_info

    # Calculate scale conversion (same as old _add_grid_lines method)
    dpi = 96.0
    scalefactor = 1.0
    scalemult = dpi * scalefactor / conversion

    print(f"✓ Scale multiplier: {scalemult}")

    # Test a few grid positions to verify they would align with ruler ticks
    test_positions = [0.0, 1.0, 2.0, 5.0, 10.0]
    print("Testing grid positions that should align with ruler major ticks:")

    for pos in test_positions:
        # Check if this position would be a major tick with label (same logic as old system)
        is_major_tick = abs(math.floor(pos / labelspacing + 1e-6) - pos / labelspacing) < 1e-3
        scene_pos = pos * scalemult
        print(f"  Position {pos}: scene={scene_pos}, is_major_tick={is_major_tick}")

    print("\n" + "="*60)
    print("GRID-RULER ALIGNMENT TEST RESULTS:")
    if alignment_ok:
        print("✅ PASS: Grid and ruler systems use identical spacing calculations")
        print("✅ Grid lines should now align perfectly with ruler tick marks")
    else:
        print("❌ FAIL: Grid and ruler systems still use different calculations")
        print("❌ Alignment issues may persist")
    print("="*60)

    return alignment_ok

if __name__ == "__main__":
    success = test_grid_ruler_alignment()
    if success:
        print("\n🎉 Grid-ruler alignment fix verified! The issue should be resolved.")
    else:
        print("\n❌ Grid-ruler alignment test failed. Further investigation needed.")
    sys.exit(0 if success else 1)
