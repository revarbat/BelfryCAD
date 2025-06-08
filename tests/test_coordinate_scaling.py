#!/usr/bin/env python3
"""
Test coordinate scaling functionality after moving it to CadScene
"""

import sys
import os

# Add the parent directory to the path so we can import BelfryCAD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from BelfryCAD.gui.cad_scene import CadScene

def test_coordinate_scaling():
    """Test that coordinate scaling works correctly in CadScene"""
    app = QApplication([])
    
    # Create a CadScene instance
    scene = CadScene()
    
    # Test basic scaling
    coords = [0, 0, 10, 10]  # Simple square in CAD coordinates
    scaled = scene.scale_coords(coords)
    
    print(f"Original coordinates: {coords}")
    print(f"Scaled coordinates: {scaled}")
    
    # Test descaling
    descaled = scene.descale_coords(scaled)
    print(f"Descaled coordinates: {descaled}")
    
    # Check if roundtrip is accurate
    tolerance = 1e-6
    for i in range(len(coords)):
        diff = abs(coords[i] - descaled[i])
        if diff > tolerance:
            print(f"ERROR: Roundtrip failed at index {i}: {coords[i]} != {descaled[i]} (diff: {diff})")
            return False
    
    print("✅ Coordinate scaling roundtrip test PASSED")
    
    # Test drawing with scaling
    try:
        # Draw a line using the new scaled addLine method
        line_item = scene.addLine(0, 0, 100, 100)  # CAD coordinates
        print(f"✅ Line drawing with scaling PASSED: {line_item}")
        
        # Draw a rectangle using the new scaled addRect method
        rect_item = scene.addRect(50, 50, 100, 100)  # CAD coordinates
        print(f"✅ Rectangle drawing with scaling PASSED: {rect_item}")
        
        # Draw an ellipse using the new scaled addEllipse method
        ellipse_item = scene.addEllipse(0, 0, 50, 50)  # CAD coordinates
        print(f"✅ Ellipse drawing with scaling PASSED: {ellipse_item}")
        
    except Exception as e:
        print(f"❌ Drawing test FAILED: {e}")
        return False
    
    print("✅ All coordinate scaling tests PASSED")
    return True

if __name__ == "__main__":
    if test_coordinate_scaling():
        print("\n🎉 Coordinate scaling migration SUCCESSFUL!")
        sys.exit(0)
    else:
        print("\n💥 Coordinate scaling migration FAILED!")
        sys.exit(1)
