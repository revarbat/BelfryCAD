#!/usr/bin/env python3
"""
Test to analyze the actual ratio between grid lines and ruler tickmarks
"""

import sys
import math
from PySide6.QtWidgets import QApplication, QGraphicsView
from PySide6.QtCore import QRectF
from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def test_grid_ruler_ratio():
    """Analyze the ratio between grid lines and ruler tickmarks"""
    print("Testing grid-ruler ratio...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create scene and view for testing
    from PySide6.QtWidgets import QGraphicsScene
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    # Set up scene rectangle
    scene.setSceneRect(-300, -300, 600, 600)
    
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
    
    # Get grid info
    grid_info = ruler.get_grid_info()
    (minorspacing, majorspacing, superspacing, labelspacing,
     divisor, units, formatfunc, conversion) = grid_info
    
    print(f"\nGrid spacing values:")
    print(f"  minorspacing = {minorspacing}")
    print(f"  majorspacing = {majorspacing}")
    print(f"  superspacing = {superspacing}")
    print(f"  labelspacing = {labelspacing}")
    
    # Calculate scale conversion
    dpi = 96.0
    scalefactor = 1.0
    scalemult = dpi * scalefactor / conversion
    print(f"  scalemult = {scalemult}")
    
    # Draw the grid using DrawingManager
    drawing_manager.redraw_grid()
    grid_items = scene.items()
    
    # Extract all vertical grid line positions
    minor_positions = []
    major_positions = []
    super_positions = []
    
    for item in grid_items:
        if hasattr(item, 'zValue') and hasattr(item, 'line'):
            line = item.line()
            z = item.zValue()
            
            # Check if it's a vertical line (x1 == x2)
            if abs(line.x1() - line.x2()) < 0.001:
                x_pos = line.x1()
                if z == -8:  # Minor lines
                    minor_positions.append(x_pos)
                elif z == -7:  # Major lines
                    major_positions.append(x_pos)
                elif z == -6:  # Super lines
                    super_positions.append(x_pos)
    
    # Sort positions
    minor_positions = sorted(list(set(minor_positions)))
    major_positions = sorted(list(set(major_positions)))
    super_positions = sorted(list(set(super_positions)))
    
    print(f"\nGrid line counts:")
    print(f"  Minor lines: {len(minor_positions)}")
    print(f"  Major lines: {len(major_positions)}")
    print(f"  Super lines: {len(super_positions)}")
    
    # Calculate expected ruler major tick positions
    scene_rect = scene.sceneRect()
    x_start_ruler = scene_rect.left() / scalemult
    x_end_ruler = scene_rect.right() / scalemult
    
    expected_ruler_ticks = []
    x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
    while x <= x_end_ruler:
        # Check if this position would be a major tick with label
        if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
            x_scene = x * scalemult
            expected_ruler_ticks.append(x_scene)
        x += minorspacing
    
    expected_ruler_ticks = sorted(list(set(expected_ruler_ticks)))
    print(f"  Expected ruler major ticks: {len(expected_ruler_ticks)}")
    
    # Analyze the ratios in a visible range
    print(f"\nAnalyzing ratios in visible range:")
    visible_min = -200  # Scene coordinates
    visible_max = 200
    
    visible_minor = [pos for pos in minor_positions if visible_min <= pos <= visible_max]
    visible_major = [pos for pos in major_positions if visible_min <= pos <= visible_max]
    visible_ruler = [pos for pos in expected_ruler_ticks if visible_min <= pos <= visible_max]
    
    print(f"  Visible minor lines: {len(visible_minor)}")
    print(f"  Visible major lines: {len(visible_major)}")
    print(f"  Visible ruler ticks: {len(visible_ruler)}")
    
    # Check if major lines align with ruler ticks
    aligned_count = 0
    for ruler_pos in visible_ruler:
        closest_major = min(visible_major, key=lambda x: abs(x - ruler_pos))
        if abs(closest_major - ruler_pos) < 0.001:
            aligned_count += 1
    
    print(f"  Aligned major lines with ruler ticks: {aligned_count}/{len(visible_ruler)}")
    
    # Calculate the ratio
    if len(visible_ruler) > 0:
        minor_to_ruler_ratio = len(visible_minor) / len(visible_ruler)
        major_to_ruler_ratio = len(visible_major) / len(visible_ruler)
        print(f"\nRatio analysis:")
        print(f"  Minor gridlines per ruler tick: {minor_to_ruler_ratio:.2f}")
        print(f"  Major gridlines per ruler tick: {major_to_ruler_ratio:.2f}")
        
        # Check if this matches the user's report of "4 gridlines for every 3 ruler ticks"
        expected_ratio = 4/3  # ≈ 1.33
        if abs(minor_to_ruler_ratio - expected_ratio) < 0.1:
            print(f"  ⚠️  MATCHES USER REPORT: ~{expected_ratio:.2f} minor gridlines per ruler tick")
        else:
            print(f"  ✓ Does not match user report of {expected_ratio:.2f}")
    
    # Sample a specific range to see the exact pattern
    print(f"\nDetailed analysis around origin:")
    center_range = 100  # ±100 scene units
    
    print("Positions within ±100 units of origin:")
    center_minor = [pos for pos in visible_minor if -center_range <= pos <= center_range]
    center_major = [pos for pos in visible_major if -center_range <= pos <= center_range]
    center_ruler = [pos for pos in visible_ruler if -center_range <= pos <= center_range]
    
    print(f"Minor positions: {[round(pos, 1) for pos in center_minor[:10]]}{'...' if len(center_minor) > 10 else ''}")
    print(f"Major positions: {[round(pos, 1) for pos in center_major[:10]]}{'...' if len(center_major) > 10 else ''}")
    print(f"Ruler positions: {[round(pos, 1) for pos in center_ruler[:10]]}{'...' if len(center_ruler) > 10 else ''}")
    
    return len(visible_minor), len(visible_ruler)

if __name__ == "__main__":
    test_grid_ruler_ratio()
