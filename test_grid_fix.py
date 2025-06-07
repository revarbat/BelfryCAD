#!/usr/bin/env python3
"""
Test script to verify that the grid fix works correctly.
This script tests that old gray grid lines (Z-value -1001) are properly removed
when the new multi-level grid system is activated.
"""

import sys
import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext

def test_grid_fix():
    """Test that old grid items are properly removed by new grid system"""
    print("Testing grid fix...")
    
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
    
    # First, simulate the old grid system by adding some items with Z-value -1001
    print("Adding old grid lines (Z-value -1001)...")
    old_grid_pen = QPen(QColor(200, 200, 200))  # Light gray
    old_grid_pen.setWidth(1)
    old_grid_pen.setStyle(Qt.PenStyle.DotLine)
    
    # Add some vertical old grid lines
    for x in range(-400, 500, 100):
        grid_line = scene.addLine(x, -500, x, 500, old_grid_pen)
        grid_line.setZValue(-1001)  # Old grid Z-value
    
    # Add some horizontal old grid lines  
    for y in range(-400, 500, 100):
        grid_line = scene.addLine(-500, y, 500, y, old_grid_pen)
        grid_line.setZValue(-1001)  # Old grid Z-value
    
    # Count old grid items
    old_grid_count = len([item for item in scene.items() 
                         if hasattr(item, 'zValue') and item.zValue() == -1001])
    print(f"✓ Added {old_grid_count} old grid lines")
    
    # Now test the new grid system - it should remove the old items
    print("Activating new grid system...")
    try:
        drawing_manager.redraw_grid()
        print("✓ New grid system activated successfully")
    except Exception as e:
        print(f"✗ New grid system failed: {e}")
        return False
    
    # Check that old grid items are gone
    remaining_old_grid = len([item for item in scene.items() 
                             if hasattr(item, 'zValue') and item.zValue() == -1001])
    print(f"✓ Old grid items remaining: {remaining_old_grid}")
    
    # Count new grid items (should have negative Z-values between -6 and -10)
    new_grid_count = len([item for item in scene.items() 
                         if hasattr(item, 'zValue') and -10 <= item.zValue() < 0])
    print(f"✓ New grid items created: {new_grid_count}")
    
    # Verify the fix worked
    if remaining_old_grid == 0:
        print("🎉 SUCCESS: All old grid items were properly removed!")
        result = True
    else:
        print(f"❌ FAILURE: {remaining_old_grid} old grid items still remain")
        result = False
    
    if new_grid_count > 0:
        print(f"✓ New multi-level grid system is working ({new_grid_count} items)")
    else:
        print("⚠️  WARNING: New grid system didn't create any items")
        result = False
    
    print("\n" + "="*60)
    print("GRID FIX TEST RESULTS:")
    print(f"- Old grid items removed: {old_grid_count - remaining_old_grid}/{old_grid_count}")
    print(f"- New grid items created: {new_grid_count}")
    print(f"- Test result: {'PASS' if result else 'FAIL'}")
    print("="*60)
    
    return result

if __name__ == "__main__":
    success = test_grid_fix()
    if success:
        print("\n🎉 Grid fix test passed! The issue is resolved.")
    else:
        print("\n❌ Grid fix test failed. The issue persists.")
    sys.exit(0 if success else 1)
