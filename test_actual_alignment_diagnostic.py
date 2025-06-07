#!/usr/bin/env python3
"""
Diagnostic script to investigate the new misalignment issue.
This script will create a visual representation to understand what's happening
in the actual application vs our test environment.
"""

import sys
import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QMainWindow, QVBoxLayout, QWidget

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def create_diagnostic_window():
    """Create a visual diagnostic window showing grid-ruler alignment"""
    print("Creating diagnostic window to visualize alignment...")

    # Create Qt application
    app = QApplication(sys.argv)

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("Grid-Ruler Alignment Diagnostic")
    main_window.setGeometry(100, 100, 1200, 800)

    # Create central widget and layout
    central_widget = QWidget()
    main_window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    # Create scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    layout.addWidget(view)

    # Set up scene rectangle (matching typical application usage)
    scene.setSceneRect(-400, -300, 800, 600)

    # Create drawing context matching application settings
    context = DrawingContext(
        scene=scene,
        dpi=96.0,
        scale_factor=1.0,
        show_grid=True,
        show_origin=True
    )

    # Create drawing manager
    drawing_manager = DrawingManager(context)

    # Create rulers for comparison
    horizontal_ruler = RulerWidget(view, "horizontal")
    vertical_ruler = RulerWidget(view, "vertical")

    print("✓ Components created")

    # Get grid info from both systems
    drawing_grid_info = drawing_manager._get_grid_info()
    ruler_grid_info = horizontal_ruler.get_grid_info()

    print("\n=== GRID INFO COMPARISON ===")
    print(f"DrawingManager: {drawing_grid_info}")
    print(f"Ruler:          {ruler_grid_info}")
    print(f"Match: {drawing_grid_info == ruler_grid_info}")

    # Draw the grid using DrawingManager
    print("\n=== DRAWING GRID ===")
    try:
        drawing_manager.redraw_grid()
        print("✓ Grid drawn successfully")
    except Exception as e:
        print(f"✗ Grid drawing failed: {e}")
        return False

    # Count grid items
    all_items = scene.items()
    grid_items = [item for item in all_items if hasattr(item, 'zValue') and item.zValue() < 0]

    print(f"✓ Total grid items: {len(grid_items)}")

    # Analyze grid line positions
    print("\n=== GRID LINE ANALYSIS ===")

    # Extract grid line positions by Z-level
    minor_lines = []  # Z-level -8
    major_lines = []  # Z-level -7
    super_lines = []  # Z-level -6

    for item in grid_items:
        z_val = item.zValue()
        if hasattr(item, 'line'):
            line = item.line()
            if z_val == -8:
                minor_lines.append(line)
            elif z_val == -7:
                major_lines.append(line)
            elif z_val == -6:
                super_lines.append(line)

    print(f"Minor lines (Z=-8): {len(minor_lines)}")
    print(f"Major lines (Z=-7): {len(major_lines)}")
    print(f"Super lines (Z=-6): {len(super_lines)}")

    # Calculate expected ruler tick positions
    print("\n=== RULER TICK CALCULATION ===")
    (minorspacing, majorspacing, superspacing, labelspacing,
     divisor, units, formatfunc, conversion) = ruler_grid_info

    dpi = 96.0
    scalefactor = 1.0
    scalemult = dpi * scalefactor / conversion

    print(f"Grid spacing: minor={minorspacing}, major={majorspacing}, super={superspacing}")
    print(f"Scale multiplier: {scalemult}")

    # Calculate expected major tick positions using OLD METHOD (exact ruler logic)
    scene_rect = scene.sceneRect()
    x_start_ruler = scene_rect.left() / scalemult
    x_end_ruler = scene_rect.right() / scalemult

    expected_major_x_positions = []
    # Use EXACT same logic as the old _add_grid_lines method
    x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
    while x <= x_end_ruler:
        # Test if this position would be a major tick with label
        if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
            x_scene = x * scalemult
            expected_major_x_positions.append(x_scene)
        x += minorspacing

    print(f"Expected major X positions: {len(expected_major_x_positions)}")
    for i, pos in enumerate(expected_major_x_positions[:10]):  # Show first 10
        print(f"  {i}: {pos:.6f}")

    # Find actual major grid line positions (vertical lines)
    actual_major_x_positions = []
    for line in major_lines:
        if abs(line.x1() - line.x2()) < 1e-6:  # Vertical line
            actual_major_x_positions.append(line.x1())

    actual_major_x_positions.sort()
    print(f"Actual major X positions: {len(actual_major_x_positions)}")
    for i, pos in enumerate(actual_major_x_positions[:10]):  # Show first 10
        print(f"  {i}: {pos:.6f}")

    # Compare positions
    print("\n=== ALIGNMENT ANALYSIS ===")
    alignment_errors = []

    for i, (expected, actual) in enumerate(zip(expected_major_x_positions, actual_major_x_positions)):
        error = abs(expected - actual)
        alignment_errors.append(error)
        if error > 0.001:  # More than 0.001 pixel error
            print(f"Position {i}: Expected {expected:.6f}, Actual {actual:.6f}, Error {error:.6f}")

    if alignment_errors:
        max_error = max(alignment_errors)
        avg_error = sum(alignment_errors) / len(alignment_errors)
        print(f"Max alignment error: {max_error:.6f} pixels")
        print(f"Average alignment error: {avg_error:.6f} pixels")

        if max_error < 0.001:
            print("✅ PERFECT ALIGNMENT: All grid lines align with ruler ticks!")
        elif max_error < 0.1:
            print("⚠️  MINOR MISALIGNMENT: Small errors detected")
        else:
            print("❌ SIGNIFICANT MISALIGNMENT: Major errors detected")
    else:
        print("❌ NO ALIGNMENT DATA: Could not compare positions")

    # Add visual markers for expected positions
    print("\n=== ADDING VISUAL MARKERS ===")
    marker_pen = QPen(QColor(255, 0, 255))  # Magenta markers
    marker_pen.setWidth(3)

    for pos in expected_major_x_positions:
        # Add small horizontal marker at expected position
        marker = scene.addLine(pos, scene_rect.top() + 10, pos, scene_rect.top() + 30, marker_pen)
        marker.setZValue(10)  # On top of everything

    print("✓ Added magenta markers at expected ruler tick positions")
    print("✓ If grid is properly aligned, major grid lines should match magenta markers")

    # Show the window
    main_window.show()

    print("\n=== DIAGNOSTIC COMPLETE ===")
    print("Visual window created. Check alignment between:")
    print("- Major grid lines (Z=-7)")
    print("- Magenta markers (expected ruler positions)")
    print("\nPress Ctrl+C to close.")

    try:
        return app.exec()
    except KeyboardInterrupt:
        print("\nDiagnostic interrupted by user")
        return 0

if __name__ == "__main__":
    sys.exit(create_diagnostic_window())
