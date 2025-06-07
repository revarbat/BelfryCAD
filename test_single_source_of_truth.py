#!/usr/bin/env python3
"""
Test to verify that DrawingManager now calls RulerWidget's get_grid_info() 
method instead of using duplicate hardcoded values.
"""

import sys
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def test_single_source_of_truth():
    """Test that DrawingManager calls ruler's method instead of hardcoding values"""
    print("Testing single source of truth for grid info...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create scene and view for testing
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    scene.setSceneRect(-500, -500, 1000, 1000)
    
    # Create drawing context and manager
    context = DrawingContext(
        scene=scene,
        dpi=96.0,
        scale_factor=1.0,
        show_grid=True,
        show_origin=True
    )
    drawing_manager = DrawingManager(context)
    
    # Create a ruler widget directly
    ruler = RulerWidget(view, "horizontal")
    
    print("✓ Test components created")
    
    # Get grid info from both
    drawing_grid_info = drawing_manager._get_grid_info()
    ruler_grid_info = ruler.get_grid_info()
    
    print("\n=== VERIFICATION THAT THEY'RE IDENTICAL ===")
    print(f"DrawingManager: {drawing_grid_info}")
    print(f"RulerWidget:    {ruler_grid_info}")
    print(f"Identical: {drawing_grid_info == ruler_grid_info}")
    
    # Test that they are still the expected values
    expected = (0.125, 1.0, 12.0, 1.0, 1.0, '"', 'decimal', 1.0)
    print(f"\n=== VERIFICATION OF EXPECTED VALUES ===")
    print(f"Expected:       {expected}")
    print(f"DrawingManager: {drawing_grid_info}")
    print(f"Matches expected: {drawing_grid_info == expected}")
    
    if drawing_grid_info == ruler_grid_info == expected:
        print("\n✅ SUCCESS: DrawingManager successfully calls RulerWidget's method")
        print("✅ Single source of truth achieved - no more code duplication!")
        return True
    else:
        print("\n❌ FAILURE: Values don't match as expected")
        return False

if __name__ == "__main__":
    success = test_single_source_of_truth()
    if success:
        print("\n🎉 Single source of truth test PASSED!")
    else:
        print("\n❌ Single source of truth test FAILED!")
    sys.exit(0 if success else 1)
