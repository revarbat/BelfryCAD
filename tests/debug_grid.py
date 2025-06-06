#!/usr/bin/env python3
"""
Debug test to verify grid line calculations and alignment.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from BelfryCAD.gui.rulers import RulerWidget
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene


def test_grid_calculations():
    """Test the grid spacing calculations"""
    print("=== Grid Calculation Test ===")
    
    app = QApplication(sys.argv)
    
    # Create a dummy graphics view and scene
    scene = QGraphicsScene()
    view = QGraphicsView()
    view.setScene(scene)
    
    # Create a ruler to test grid info
    ruler = RulerWidget(view, "horizontal")
    
    # Get grid information
    (minorspacing, majorspacing, superspacing, labelspacing,
     divisor, units, formatfunc, conversion) = ruler.get_grid_info()
    
    print(f"Minor spacing: {minorspacing}")
    print(f"Major spacing: {majorspacing}")
    print(f"Super spacing: {superspacing}")
    print(f"Label spacing: {labelspacing}")
    print(f"Divisor: {divisor}")
    print(f"Units: {units}")
    print(f"Format function: {formatfunc}")
    print(f"Conversion: {conversion}")
    
    print("\n=== Grid Line Positions (for range -5 to 5) ===")
    
    import math
    x_start = -5
    x_end = 5
    first_x = math.floor(x_start / labelspacing) * labelspacing
    
    print(f"Starting from: {first_x}")
    
    x = first_x
    grid_positions = []
    while x <= x_end:
        # Check if this would be a major tick (matches ruler logic)
        if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
            grid_positions.append(x)
            print(f"Grid line at: {x}")
        x += labelspacing
    
    print(f"\nTotal grid lines in range: {len(grid_positions)}")
    print(f"Grid positions: {grid_positions}")
    
    # Test the major tick detection logic
    print("\n=== Major Tick Detection Test ===")
    test_positions = [-2.0, -1.0, 0.0, 1.0, 2.0, 0.5, 1.5]
    for pos in test_positions:
        is_major = abs(math.floor(pos / labelspacing + 1e-6) - pos / labelspacing) < 1e-3
        print(f"Position {pos}: {'MAJOR TICK' if is_major else 'not major'}")
    
    app.quit()


if __name__ == "__main__":
    test_grid_calculations()
