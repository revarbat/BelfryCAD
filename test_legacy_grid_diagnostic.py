#!/usr/bin/env python3
"""
Diagnostic test to identify if legacy grid system (Z-value -1001) is still active
and causing the reported 4:3 grid-to-ruler ratio issue.
"""

import sys
import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def check_legacy_grid_system():
    """Check if legacy grid system is still active and analyze all grid systems"""
    print("Checking for legacy grid system and analyzing all visible grid elements...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setWindowTitle("Legacy Grid System Diagnostic")
    view.resize(1000, 800)
    
    # Set up scene rectangle
    scene.setSceneRect(-300, -300, 600, 600)
    view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
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
    
    print("✓ Components created")
    
    # Get grid info
    grid_info = ruler.get_grid_info()
    (minorspacing, majorspacing, superspacing, labelspacing,
     divisor, units, formatfunc, conversion) = grid_info
    
    # Calculate scale conversion
    dpi = 96.0
    scalefactor = 1.0
    scalemult = dpi * scalefactor / conversion
    
    print(f"\nGrid specifications:")
    print(f"  minorspacing = {minorspacing} units ({minorspacing * scalemult:.1f} px)")
    print(f"  majorspacing = {majorspacing} units ({majorspacing * scalemult:.1f} px)")
    print(f"  labelspacing = {labelspacing} units ({labelspacing * scalemult:.1f} px)")
    print(f"  scalemult = {scalemult}")
    
    # Check if there are any existing grid items before drawing new ones
    print(f"\n=== BEFORE DRAWING NEW GRID ===")
    initial_items = scene.items()
    print(f"Initial scene items: {len(initial_items)}")
    
    # Check for legacy grid items (Z-value -1001)
    legacy_items = [item for item in initial_items 
                   if hasattr(item, 'zValue') and item.zValue() == -1001]
    print(f"Legacy grid items (Z=-1001): {len(legacy_items)}")
    
    # Check for modern grid items (Z-values -6 to -10)
    modern_items = [item for item in initial_items 
                   if hasattr(item, 'zValue') and -10 <= item.zValue() <= -6]
    print(f"Modern grid items (Z=-6 to -10): {len(modern_items)}")
    
    # Now draw the grid using DrawingManager
    print(f"\n=== DRAWING NEW GRID ===")
    drawing_manager.redraw_grid()
    
    # Analyze all grid items after drawing
    print(f"\n=== AFTER DRAWING NEW GRID ===")
    all_items = scene.items()
    print(f"Total scene items: {len(all_items)}")
    
    # Categorize all items by Z-value
    z_value_counts = {}
    grid_items_by_z = {}
    
    for item in all_items:
        if hasattr(item, 'zValue'):
            z = item.zValue()
            z_value_counts[z] = z_value_counts.get(z, 0) + 1
            
            # Collect grid-related items
            if z <= -6:  # Grid items are typically at negative Z-values
                if z not in grid_items_by_z:
                    grid_items_by_z[z] = []
                grid_items_by_z[z].append(item)
    
    print(f"\nItems by Z-value:")
    for z in sorted(z_value_counts.keys()):
        print(f"  Z={z}: {z_value_counts[z]} items")
    
    # Analyze grid line positions for each Z-level
    print(f"\n=== GRID LINE ANALYSIS ===")
    
    scene_rect = scene.sceneRect()
    visible_range = [-200, 200]  # Focus on ±200 scene units
    
    all_vertical_lines = {}
    
    for z, items in grid_items_by_z.items():
        vertical_positions = []
        
        for item in items:
            if hasattr(item, 'line'):
                line = item.line()
                # Check if it's a vertical line
                if abs(line.x1() - line.x2()) < 0.001:
                    x_pos = line.x1()
                    if visible_range[0] <= x_pos <= visible_range[1]:
                        vertical_positions.append(x_pos)
        
        if vertical_positions:
            vertical_positions = sorted(list(set(vertical_positions)))
            all_vertical_lines[z] = vertical_positions
            print(f"\nZ-level {z}: {len(vertical_positions)} vertical lines")
            print(f"  Positions: {[round(pos, 1) for pos in vertical_positions[:10]]}" + 
                  ("..." if len(vertical_positions) > 10 else ""))
            
            # Calculate spacing between consecutive lines
            if len(vertical_positions) >= 2:
                spacings = []
                for i in range(len(vertical_positions) - 1):
                    spacing = vertical_positions[i+1] - vertical_positions[i]
                    spacings.append(spacing)
                
                if spacings:
                    avg_spacing = sum(spacings) / len(spacings)
                    print(f"  Average spacing: {avg_spacing:.2f} px ({avg_spacing/scalemult:.4f} units)")
    
    # Calculate expected ruler major tick positions
    print(f"\n=== RULER TICK ANALYSIS ===")
    x_start_ruler = visible_range[0] / scalemult
    x_end_ruler = visible_range[1] / scalemult
    
    ruler_major_ticks = []
    x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
    while x <= x_end_ruler:
        if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
            x_scene = x * scalemult
            ruler_major_ticks.append(x_scene)
        x += minorspacing
    
    ruler_major_ticks = sorted(list(set(ruler_major_ticks)))
    print(f"Expected ruler major ticks: {len(ruler_major_ticks)}")
    print(f"  Positions: {[round(pos, 1) for pos in ruler_major_ticks[:10]]}" + 
          ("..." if len(ruler_major_ticks) > 10 else ""))
    
    if len(ruler_major_ticks) >= 2:
        ruler_spacings = []
        for i in range(len(ruler_major_ticks) - 1):
            spacing = ruler_major_ticks[i+1] - ruler_major_ticks[i]
            ruler_spacings.append(spacing)
        
        if ruler_spacings:
            avg_ruler_spacing = sum(ruler_spacings) / len(ruler_spacings)
            print(f"  Average spacing: {avg_ruler_spacing:.2f} px ({avg_ruler_spacing/scalemult:.4f} units)")
    
    # Calculate ratios for each grid level
    print(f"\n=== RATIO ANALYSIS ===")
    user_expected_ratio = 4.0/3.0  # ≈ 1.33
    print(f"User reported ratio: 4:3 = {user_expected_ratio:.3f}")
    
    for z, positions in all_vertical_lines.items():
        if len(ruler_major_ticks) > 0:
            ratio = len(positions) / len(ruler_major_ticks)
            print(f"\nZ-level {z} analysis:")
            print(f"  Grid lines: {len(positions)}")
            print(f"  Ruler ticks: {len(ruler_major_ticks)}")
            print(f"  Ratio: {ratio:.3f}")
            
            if abs(ratio - user_expected_ratio) < 0.15:
                print(f"  ⚠️  MATCHES USER REPORT! ({user_expected_ratio:.3f})")
                
                # This might be the source of the issue
                print(f"  🔍 POTENTIAL ISSUE SOURCE:")
                print(f"     This Z-level shows the 4:3 ratio the user reported")
                
                # Check if this is a legacy system
                if z == -1001:
                    print(f"     ❌ This is the LEGACY GRID SYSTEM (Z=-1001)")
                    print(f"     ❌ Legacy grid should have been removed!")
                elif z in [-8, -7, -6]:
                    print(f"     ✓ This is the modern grid system")
                    print(f"     ⚠️  Modern grid showing unexpected ratio")
            else:
                print(f"  ✓ Different from user report")
    
    # Check alignment between systems
    print(f"\n=== ALIGNMENT CHECK ===")
    if -7 in all_vertical_lines:  # Major grid lines
        major_grid_positions = all_vertical_lines[-7]
        aligned_count = 0
        
        for ruler_pos in ruler_major_ticks:
            closest_grid = min(major_grid_positions, key=lambda x: abs(x - ruler_pos))
            if abs(closest_grid - ruler_pos) < 0.001:
                aligned_count += 1
        
        print(f"Major grid alignment: {aligned_count}/{len(ruler_major_ticks)} ({100*aligned_count/len(ruler_major_ticks):.1f}%)")
    
    # Add visual markers to the scene for diagnosis
    print(f"\n=== ADDING VISUAL MARKERS ===")
    
    # Add ruler tick markers (red circles)
    for pos in ruler_major_ticks:
        if visible_range[0] <= pos <= visible_range[1]:
            circle = scene.addEllipse(pos - 3, -5, 6, 6, 
                                    QPen(QColor("red"), 2), 
                                    QBrush(QColor("red")))
            circle.setZValue(10)
            
            text = scene.addText("R", QFont("Arial", 8))
            text.setPos(pos - 3, 5)
            text.setDefaultTextColor(QColor("red"))
            text.setZValue(10)
    
    # Add grid line markers for each Z-level (different colors)
    colors = {-8: "green", -7: "blue", -6: "cyan", -1001: "orange"}
    shapes = {-8: "circle", -7: "square", -6: "diamond", -1001: "triangle"}
    
    y_offset = 15
    for z, positions in all_vertical_lines.items():
        if z in colors:
            color = colors[z]
            for pos in positions:
                if visible_range[0] <= pos <= visible_range[1]:
                    if shapes[z] == "square":
                        rect = scene.addRect(pos - 2, y_offset, 4, 4,
                                           QPen(QColor(color), 1),
                                           QBrush(QColor(color)))
                        rect.setZValue(10)
                    else:
                        circle = scene.addEllipse(pos - 2, y_offset, 4, 4,
                                                QPen(QColor(color), 1),
                                                QBrush(QColor(color)))
                        circle.setZValue(10)
        y_offset += 10
    
    # Add legend
    legend_text = [
        "DIAGNOSTIC LEGEND:",
        "Red circles (R) = Ruler major ticks",
        "Blue squares = Major grid (Z=-7)",
        "Green circles = Minor grid (Z=-8)",
        "Cyan circles = Super grid (Z=-6)",
        "Orange triangles = Legacy grid (Z=-1001)",
        "",
        f"Expected: Perfect alignment between red and blue",
        f"User report: 4:3 ratio = {user_expected_ratio:.3f}"
    ]
    
    legend_display = scene.addText("\n".join(legend_text), QFont("Arial", 10))
    legend_display.setPos(-290, -280)
    legend_display.setDefaultTextColor(QColor("darkBlue"))
    legend_display.setZValue(10)
    
    # Show the diagnostic window
    print(f"\nShowing diagnostic window...")
    view.show()
    
    # Set up a timer to close after inspection
    def close_window():
        print("\nDiagnostic complete. Window closing...")
        view.close()
        app.quit()
    
    # Keep window open for 45 seconds for inspection
    QTimer.singleShot(45000, close_window)
    
    # Return diagnostic data
    result = {
        'legacy_items': len(legacy_items),
        'modern_items': len(modern_items),
        'total_items': len(all_items),
        'z_value_counts': z_value_counts,
        'grid_line_counts': {z: len(positions) for z, positions in all_vertical_lines.items()},
        'ruler_tick_count': len(ruler_major_ticks),
        'ratios': {z: len(positions)/len(ruler_major_ticks) if len(ruler_major_ticks) > 0 else 0 
                  for z, positions in all_vertical_lines.items()},
        'user_ratio_matches': {z: abs(len(positions)/len(ruler_major_ticks) - user_expected_ratio) < 0.15 
                              if len(ruler_major_ticks) > 0 else False
                              for z, positions in all_vertical_lines.items()}
    }
    
    print(f"\n" + "="*60)
    print("DIAGNOSTIC SUMMARY:")
    print(f"Legacy grid items (Z=-1001): {result['legacy_items']}")
    print(f"Modern grid items: {result['modern_items']}")
    print(f"Total scene items: {result['total_items']}")
    
    if result['legacy_items'] > 0:
        print(f"⚠️  WARNING: Legacy grid system still active!")
        print(f"   This could be causing the 4:3 ratio issue")
    
    for z, ratio in result['ratios'].items():
        print(f"Z-level {z} ratio: {ratio:.3f}")
        if result['user_ratio_matches'][z]:
            print(f"  ⚠️  MATCHES USER REPORT!")
    
    print("="*60)
    
    # Run the Qt event loop
    app.exec()
    
    return result

if __name__ == "__main__":
    try:
        result = check_legacy_grid_system()
        
        print(f"\n" + "="*60)
        print("FINAL ANALYSIS:")
        
        # Check if legacy system is the issue
        if result['legacy_items'] > 0:
            print("❌ ISSUE IDENTIFIED: Legacy grid system (Z=-1001) is still active")
            print("   This is likely causing the 4:3 ratio observation")
            print("   Recommendation: Ensure legacy grid removal is working properly")
        else:
            print("✓ Legacy grid system properly removed")
            
            # Check if modern system has unexpected ratios
            found_issue = False
            for z, matches in result['user_ratio_matches'].items():
                if matches:
                    print(f"⚠️  Modern grid Z-level {z} shows 4:3 ratio")
                    print(f"   This needs investigation")
                    found_issue = True
            
            if not found_issue:
                print("✓ No systems show 4:3 ratio")
                print("   The reported issue may be context-specific")
        
        print("="*60)
        
    except Exception as e:
        print(f"Error in diagnostic: {e}")
        import traceback
        traceback.print_exc()
