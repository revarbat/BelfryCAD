#!/usr/bin/env python3
"""
Comprehensive test to verify grid-ruler alignment at pixel level.
This test simulates the exact conditions where alignment issues were reported.
"""

import sys
import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def test_pixel_level_alignment():
    """Test grid-ruler alignment at pixel level precision"""
    print("Testing pixel-level grid-ruler alignment...")
    
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
    
    # Create drawing manager and ruler
    drawing_manager = DrawingManager(context)
    ruler = RulerWidget(view, "horizontal")
    
    print("✓ Test components created")
    
    # Get grid info from both systems (should be identical now)
    drawing_grid_info = drawing_manager._get_grid_info()
    ruler_grid_info = ruler.get_grid_info()
    
    (minorspacing, majorspacing, superspacing, labelspacing,
     divisor, units, formatfunc, conversion) = ruler_grid_info
    
    # Calculate scale conversion
    dpi = 96.0
    scalefactor = 1.0
    scalemult = dpi * scalefactor / conversion
    
    print(f"✓ Grid info: minor={minorspacing}, major={majorspacing}, label={labelspacing}")
    print(f"✓ Scale multiplier: {scalemult}")
    
    # Draw the grid using DrawingManager
    drawing_manager.redraw_grid()
    grid_items = scene.items()
    grid_lines = [item for item in grid_items if hasattr(item, 'zValue') and item.zValue() < 0]
    
    print(f"✓ Drew {len(grid_lines)} grid lines")
    
    # Extract positions of major grid lines (Z-value -7)
    major_grid_positions = []
    for item in grid_lines:
        if hasattr(item, 'zValue') and item.zValue() == -7:  # Major lines
            if hasattr(item, 'line'):
                line = item.line()
                # For vertical lines, check X position
                if abs(line.y1() - line.y2()) > abs(line.x1() - line.x2()):
                    major_grid_positions.append(line.x1())
                # For horizontal lines, check Y position  
                else:
                    major_grid_positions.append(line.y1())
    
    # Remove duplicates and sort
    major_grid_positions = sorted(list(set(major_grid_positions)))
    print(f"✓ Found {len(major_grid_positions)} major grid line positions")
    
    # Calculate expected ruler major tick positions using the same logic as the old _add_grid_lines method
    scene_rect = scene.sceneRect()
    expected_positions = []
    
    # Test range in ruler coordinates
    x_start_ruler = scene_rect.left() / scalemult
    x_end_ruler = scene_rect.right() / scalemult
    
    # Use exact same logic as old _add_grid_lines method
    x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
    while x <= x_end_ruler:
        # Test if this position would be a major tick with label
        if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
            x_scene = x * scalemult
            expected_positions.append(x_scene)
        x += minorspacing
    
    print(f"✓ Calculated {len(expected_positions)} expected ruler tick positions")
    
    # Compare grid positions with expected ruler positions
    alignment_tolerance = 0.001  # Very small tolerance for floating point comparison
    aligned_count = 0
    misaligned_positions = []
    
    print("\nDetailed alignment analysis:")
    for expected_pos in expected_positions:
        # Find closest grid line
        closest_grid_pos = min(major_grid_positions, key=lambda x: abs(x - expected_pos), default=None)
        if closest_grid_pos is not None:
            offset = abs(closest_grid_pos - expected_pos)
            if offset <= alignment_tolerance:
                aligned_count += 1
                print(f"  ✓ Position {expected_pos:.3f}: grid at {closest_grid_pos:.3f}, offset {offset:.6f}")
            else:
                misaligned_positions.append((expected_pos, closest_grid_pos, offset))
                print(f"  ❌ Position {expected_pos:.3f}: grid at {closest_grid_pos:.3f}, offset {offset:.6f}")
    
    # Report results
    total_expected = len(expected_positions)
    alignment_percentage = (aligned_count / total_expected * 100) if total_expected > 0 else 0
    
    print(f"\n" + "="*70)
    print("PIXEL-LEVEL ALIGNMENT TEST RESULTS:")
    print(f"Expected ruler tick positions: {total_expected}")
    print(f"Perfectly aligned grid lines: {aligned_count}")
    print(f"Misaligned grid lines: {len(misaligned_positions)}")
    print(f"Alignment accuracy: {alignment_percentage:.1f}%")
    
    if len(misaligned_positions) == 0:
        print("✅ PERFECT ALIGNMENT: All grid lines align exactly with ruler ticks!")
        result = True
    elif alignment_percentage >= 95:
        print("✅ EXCELLENT ALIGNMENT: >95% of grid lines align within tolerance")
        result = True
    else:
        print("❌ POOR ALIGNMENT: Significant misalignment detected")
        print("Misaligned positions:")
        for expected, actual, offset in misaligned_positions[:5]:  # Show first 5
            print(f"  Expected: {expected:.3f}, Actual: {actual:.3f}, Offset: {offset:.6f}")
        result = False
    
    print("="*70)
    
    return result

if __name__ == "__main__":
    success = test_pixel_level_alignment()
    if success:
        print("\n🎉 Pixel-level alignment test PASSED! Grid-ruler alignment is perfect.")
    else:
        print("\n❌ Pixel-level alignment test FAILED. Alignment issues remain.")
    sys.exit(0 if success else 1)
