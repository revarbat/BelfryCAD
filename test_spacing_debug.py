#!/usr/bin/env python3
"""
Quick test to understand the difference between major and label spacing
"""

import sys
from PySide6.QtWidgets import QApplication
from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def test_spacing_values():
    app = QApplication(sys.argv)
    
    # Create a dummy ruler
    ruler = RulerWidget(None, "horizontal")
    grid_info = ruler.get_grid_info()
    
    (minorspacing, majorspacing, superspacing, labelspacing,
     divisor, units, formatfunc, conversion) = grid_info
    
    print("Grid spacing values:")
    print(f"  minorspacing = {minorspacing}")
    print(f"  majorspacing = {majorspacing}")
    print(f"  superspacing = {superspacing}")
    print(f"  labelspacing = {labelspacing}")
    
    print(f"\nThe old method used labelspacing ({labelspacing}) for major grid calculation")
    print(f"The new method uses majorspacing ({majorspacing}) for major grid calculation")
    print(f"These are {'the same' if majorspacing == labelspacing else 'different'}!")

if __name__ == "__main__":
    test_spacing_values()
