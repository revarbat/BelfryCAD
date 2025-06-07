#!/usr/bin/env python3
"""
Test to compare the old vs new grid calculation methods
"""

import sys
import math
from PySide6.QtWidgets import QApplication
from BelfryCAD.gui.rulers import RulerWidget

def compare_grid_calculations():
    app = QApplication(sys.argv)

    # Test parameters (matching our diagnostic)
    scene_left = -400
    scene_right = 400

    # Grid info
    ruler = RulerWidget(None, "horizontal")
    grid_info = ruler.get_grid_info()
    (minorspacing, majorspacing, superspacing, labelspacing,
     divisor, units, formatfunc, conversion) = grid_info

    dpi = 96.0
    scalefactor = 1.0
    scalemult = dpi * scalefactor / conversion

    print("=== TEST PARAMETERS ===")
    print(f"Scene bounds: {scene_left} to {scene_right}")
    print(f"Scale multiplier: {scalemult}")
    print(f"minorspacing: {minorspacing}")
    print(f"majorspacing: {majorspacing}")
    print(f"labelspacing: {labelspacing}")

    # OLD METHOD (from _add_grid_lines)
    print("\n=== OLD METHOD (CORRECT) ===")
    x_start_ruler = scene_left / scalemult
    x_end_ruler = scene_right / scalemult

    print(f"CAD coordinate range: {x_start_ruler:.6f} to {x_end_ruler:.6f}")

    old_positions = []
    x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
    print(f"Starting x: {x:.6f}")

    while x <= x_end_ruler:
        # Test if this position would be a major tick with label
        if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
            x_scene = x * scalemult
            old_positions.append(x_scene)
            print(f"  Major tick at CAD {x:.6f} -> Scene {x_scene:.6f}")
        x += minorspacing

    # NEW METHOD (from _draw_grid_lines)
    print("\n=== NEW METHOD (INCORRECT) ===")
    xstart = scene_left / scalemult
    xend = scene_right / scalemult

    print(f"CAD coordinate range: {xstart:.6f} to {xend:.6f}")

    new_positions = []
    x = math.ceil(xstart / majorspacing) * majorspacing
    print(f"Starting x: {x:.6f}")

    while x <= xend:
        x_scene = x * scalemult
        new_positions.append(x_scene)
        print(f"  Major line at CAD {x:.6f} -> Scene {x_scene:.6f}")
        x += majorspacing

    # COMPARISON
    print("\n=== COMPARISON ===")
    print(f"Old method positions: {len(old_positions)}")
    print(f"New method positions: {len(new_positions)}")

    if old_positions and new_positions:
        offset = new_positions[0] - old_positions[0] if old_positions else 0
        print(f"Offset between methods: {offset:.6f} pixels")

        if abs(offset - 96.0) < 0.1:
            print("✅ This explains the 96-pixel offset in our diagnostic!")

        # Check if the issue is the starting position calculation
        old_start_calc = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
        new_start_calc = math.ceil(xstart / majorspacing) * majorspacing

        print(f"\nStarting position calculation:")
        print(f"  Old: floor({x_start_ruler:.6f} / {minorspacing}) * {minorspacing} = {old_start_calc:.6f}")
        print(f"  New: ceil({xstart:.6f} / {majorspacing}) * {majorspacing} = {new_start_calc:.6f}")
        print(f"  Difference: {new_start_calc - old_start_calc:.6f}")

if __name__ == "__main__":
    compare_grid_calculations()
