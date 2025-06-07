#!/usr/bin/env python3
"""
Simplified grid-ruler ratio analysis to understand the 4:3 ratio issue.
"""

import sys
import math
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def analyze_grid_ruler_ratios():
    """Analyze grid-ruler ratios to understand the 4:3 issue"""
    print("Analyzing grid-ruler ratios...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    # Test different scene sizes to see where the 4:3 ratio might appear
    scene_configs = [
        {"name": "Small view", "rect": (-100, -100, 200, 200)},
        {"name": "Medium view", "rect": (-200, -200, 400, 400)},
        {"name": "Large view", "rect": (-500, -500, 1000, 1000)},
        {"name": "Very small view", "rect": (-50, -50, 100, 100)},
    ]
    
    for config in scene_configs:
        print(f"\n" + "="*50)
        print(f"Testing {config['name']}: {config['rect']}")
        
        # Set up scene rectangle
        scene.setSceneRect(*config['rect'])
        
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
        
        # Get grid info
        grid_info = ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info
        
        # Calculate scale conversion
        scalemult = 96.0 * 1.0 / conversion  # dpi * scalefactor / conversion
        
        # Clear and redraw grid
        scene.clear()
        drawing_manager.redraw_grid()
        
        # Count grid lines
        grid_items = scene.items()
        minor_lines = []
        major_lines = []
        
        for item in grid_items:
            if hasattr(item, 'zValue') and hasattr(item, 'line'):
                line = item.line()
                z = item.zValue()
                
                # Check if it's a vertical line
                if abs(line.x1() - line.x2()) < 0.001:
                    x_pos = line.x1()
                    if z == -8:  # Minor lines
                        minor_lines.append(x_pos)
                    elif z == -7:  # Major lines
                        major_lines.append(x_pos)
        
        # Sort and deduplicate
        minor_lines = sorted(list(set(minor_lines)))
        major_lines = sorted(list(set(major_lines)))
        
        # Calculate expected ruler major tick positions
        scene_rect = scene.sceneRect()
        x_start_ruler = scene_rect.left() / scalemult
        x_end_ruler = scene_rect.right() / scalemult
        
        ruler_major_ticks = []
        x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
        while x <= x_end_ruler:
            if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
                x_scene = x * scalemult
                ruler_major_ticks.append(x_scene)
            x += minorspacing
        
        ruler_major_ticks = sorted(list(set(ruler_major_ticks)))
        
        print(f"  Grid lines found:")
        print(f"    Minor lines: {len(minor_lines)}")
        print(f"    Major lines: {len(major_lines)}")
        print(f"  Expected ruler major ticks: {len(ruler_major_ticks)}")
        
        # Calculate ratios
        if len(ruler_major_ticks) > 0:
            minor_to_ruler = len(minor_lines) / len(ruler_major_ticks)
            major_to_ruler = len(major_lines) / len(ruler_major_ticks)
            print(f"  Ratios:")
            print(f"    Minor/Ruler = {minor_to_ruler:.2f}")
            print(f"    Major/Ruler = {major_to_ruler:.2f}")
            
            # Check for 4:3 ratio
            user_ratio = 4.0/3.0  # ≈ 1.33
            if abs(minor_to_ruler - user_ratio) < 0.15:
                print(f"    ⚠️  CLOSE TO 4:3 RATIO! ({user_ratio:.2f})")
            
            # Look at spacing between lines
            if len(minor_lines) >= 4 and len(ruler_major_ticks) >= 3:
                print(f"  Spacing analysis:")
                
                # Find spacing between consecutive minor lines
                minor_spacings = []
                for i in range(len(minor_lines) - 1):
                    spacing = minor_lines[i+1] - minor_lines[i]
                    minor_spacings.append(spacing)
                
                # Find spacing between consecutive ruler ticks
                ruler_spacings = []
                for i in range(len(ruler_major_ticks) - 1):
                    spacing = ruler_major_ticks[i+1] - ruler_major_ticks[i]
                    ruler_spacings.append(spacing)
                
                if minor_spacings and ruler_spacings:
                    avg_minor_spacing = sum(minor_spacings) / len(minor_spacings)
                    avg_ruler_spacing = sum(ruler_spacings) / len(ruler_spacings)
                    spacing_ratio = avg_ruler_spacing / avg_minor_spacing
                    
                    print(f"    Average minor line spacing: {avg_minor_spacing:.1f} px")
                    print(f"    Average ruler tick spacing: {avg_ruler_spacing:.1f} px")
                    print(f"    Ruler spacing / Minor spacing = {spacing_ratio:.2f}")
                    
                    # Check if this gives us the 4:3 pattern
                    if abs(spacing_ratio - user_ratio) < 0.15:
                        print(f"    ⚠️  SPACING RATIO MATCHES 4:3!")
        
        # Look at the pattern around origin
        print(f"  Pattern around origin:")
        origin_range = 2 * majorspacing * scalemult  # ±2 major units
        nearby_minor = [pos for pos in minor_lines if -origin_range <= pos <= origin_range]
        nearby_major = [pos for pos in major_lines if -origin_range <= pos <= origin_range]
        nearby_ruler = [pos for pos in ruler_major_ticks if -origin_range <= pos <= origin_range]
        
        print(f"    Minor lines near origin: {[round(pos/scalemult, 3) for pos in nearby_minor]}")
        print(f"    Major lines near origin: {[round(pos/scalemult, 3) for pos in nearby_major]}")
        print(f"    Ruler ticks near origin: {[round(pos/scalemult, 3) for pos in nearby_ruler]}")

def check_different_zoom_levels():
    """Check ratios at different zoom levels"""
    print(f"\n" + "="*60)
    print("CHECKING DIFFERENT ZOOM LEVELS")
    
    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    scene.setSceneRect(-200, -200, 400, 400)
    
    zoom_levels = [0.5, 1.0, 1.5, 2.0, 3.0]
    
    for zoom in zoom_levels:
        print(f"\nTesting zoom level: {zoom}x")
        
        context = DrawingContext(
            scene=scene,
            dpi=96.0,
            scale_factor=zoom,  # Different zoom level
            show_grid=True,
            show_origin=True
        )
        
        drawing_manager = DrawingManager(context)
        ruler = RulerWidget(view, "horizontal")
        
        # Clear and redraw
        scene.clear()
        drawing_manager.redraw_grid()
        
        # Quick count
        grid_items = scene.items()
        minor_count = len([item for item in grid_items if hasattr(item, 'zValue') and item.zValue() == -8])
        major_count = len([item for item in grid_items if hasattr(item, 'zValue') and item.zValue() == -7])
        
        # Get expected ruler ticks at this zoom
        grid_info = ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info
        
        scalemult = 96.0 * zoom / conversion
        scene_rect = scene.sceneRect()
        x_start = scene_rect.left() / scalemult
        x_end = scene_rect.right() / scalemult
        
        ruler_count = 0
        x = math.floor(x_start / minorspacing + 1e-6) * minorspacing
        while x <= x_end:
            if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
                ruler_count += 1
            x += minorspacing
        
        print(f"  Grid: {minor_count} minor, {major_count} major lines")
        print(f"  Expected ruler ticks: {ruler_count}")
        if ruler_count > 0:
            minor_ratio = minor_count / ruler_count
            print(f"  Minor/Ruler ratio: {minor_ratio:.2f}")
            if abs(minor_ratio - 4.0/3.0) < 0.2:
                print(f"  ⚠️  CLOSE TO 4:3 at {zoom}x zoom!")

if __name__ == "__main__":
    try:
        analyze_grid_ruler_ratios()
        check_different_zoom_levels()
        
        print(f"\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("This test explored different view sizes and zoom levels")
        print("to identify where the 4:3 grid-to-ruler ratio might occur.")
        print("="*60)
        
    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        traceback.print_exc()
