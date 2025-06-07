#!/usr/bin/env python3
"""
Visual diagnostic to help identify the 4:3 grid-to-ruler ratio issue.
Creates a visual window showing grid lines and ruler ticks side by side.
"""

import sys
import math
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, 
                              QGraphicsTextItem, QVBoxLayout, QWidget, QLabel)

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def create_visual_diagnostic():
    """Create a visual diagnostic window to identify the grid-ruler ratio issue"""
    print("Creating visual diagnostic for grid-ruler ratio analysis...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setWindowTitle("Grid-Ruler Ratio Diagnostic")
    view.resize(800, 600)
    
    # Set up scene rectangle focused on a smaller region for clarity
    scene.setSceneRect(-200, -200, 400, 400)
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
    
    print(f"Grid spacing values:")
    print(f"  minorspacing = {minorspacing}")
    print(f"  majorspacing = {majorspacing}")
    print(f"  superspacing = {superspacing}")
    print(f"  labelspacing = {labelspacing}")
    print(f"  scalemult = {scalemult}")
    
    # Draw the grid
    print("\nDrawing grid...")
    drawing_manager.redraw_grid()
    
    # Count grid lines in the scene
    grid_items = scene.items()
    minor_lines = []
    major_lines = []
    super_lines = []
    
    for item in grid_items:
        if hasattr(item, 'zValue') and hasattr(item, 'line'):
            line = item.line()
            z = item.zValue()
            
            # Check if it's a vertical line (for horizontal position analysis)
            if abs(line.x1() - line.x2()) < 0.001:
                x_pos = line.x1()
                if z == -8:  # Minor lines
                    minor_lines.append(x_pos)
                elif z == -7:  # Major lines
                    major_lines.append(x_pos)
                elif z == -6:  # Super lines
                    super_lines.append(x_pos)
    
    # Sort positions
    minor_lines = sorted(list(set(minor_lines)))
    major_lines = sorted(list(set(major_lines)))
    super_lines = sorted(list(set(super_lines)))
    
    print(f"Found grid lines:")
    print(f"  Minor lines: {len(minor_lines)}")
    print(f"  Major lines: {len(major_lines)}")
    print(f"  Super lines: {len(super_lines)}")
    
    # Calculate expected ruler tick positions using the exact ruler logic
    scene_rect = scene.sceneRect()
    x_start_ruler = scene_rect.left() / scalemult
    x_end_ruler = scene_rect.right() / scalemult
    
    ruler_major_ticks = []
    x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing
    while x <= x_end_ruler:
        # Check if this position would be a major tick with label
        if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
            x_scene = x * scalemult
            ruler_major_ticks.append(x_scene)
        x += minorspacing
    
    ruler_major_ticks = sorted(list(set(ruler_major_ticks)))
    print(f"  Expected ruler major ticks: {len(ruler_major_ticks)}")
    
    # Add visual markers for ruler tick positions (red dots)
    for tick_pos in ruler_major_ticks:
        # Add a red circle at each ruler tick position
        circle = scene.addEllipse(tick_pos - 3, -3, 6, 6, 
                                QPen(QColor("red"), 2), 
                                QBrush(QColor("red")))
        circle.setZValue(10)  # Above everything else
        
        # Add text label
        text = scene.addText(f"R", QFont("Arial", 8))
        text.setPos(tick_pos - 3, 5)
        text.setDefaultTextColor(QColor("red"))
        text.setZValue(10)
    
    # Add visual markers for major grid line positions (blue squares)
    for grid_pos in major_lines:
        # Add a blue square at each major grid line position
        rect = scene.addRect(grid_pos - 2, 15, 4, 4,
                           QPen(QColor("blue"), 1),
                           QBrush(QColor("blue")))
        rect.setZValue(10)
        
        # Add text label
        text = scene.addText(f"G", QFont("Arial", 8))
        text.setPos(grid_pos - 3, 25)
        text.setDefaultTextColor(QColor("blue"))
        text.setZValue(10)
    
    # Add visual markers for minor grid line positions (green dots, every 4th one)
    visible_minor = [pos for pos in minor_lines if scene_rect.left() <= pos <= scene_rect.right()]
    for i, grid_pos in enumerate(visible_minor):
        if i % 4 == 0:  # Show every 4th minor line for clarity
            circle = scene.addEllipse(grid_pos - 1, -15, 2, 2,
                                    QPen(QColor("green"), 1),
                                    QBrush(QColor("green")))
            circle.setZValue(10)
    
    # Add analysis text to the scene
    info_text = []
    info_text.append(f"Grid Analysis (Scene range: {scene_rect.left():.0f} to {scene_rect.right():.0f})")
    info_text.append(f"Minor spacing: {minorspacing} units ({minorspacing * scalemult:.1f} px)")
    info_text.append(f"Major spacing: {majorspacing} units ({majorspacing * scalemult:.1f} px)")
    info_text.append(f"Label spacing: {labelspacing} units ({labelspacing * scalemult:.1f} px)")
    info_text.append(f"")
    info_text.append(f"Counts in visible area:")
    info_text.append(f"  Red dots (R) = Ruler major ticks: {len(ruler_major_ticks)}")
    info_text.append(f"  Blue squares (G) = Major grid lines: {len(major_lines)}")
    info_text.append(f"  Green dots = Minor grid lines (every 4th shown)")
    info_text.append(f"")
    
    # Focus on a specific region for ratio analysis
    analysis_range = 100  # ±100 scene units around origin
    analysis_minor = [pos for pos in minor_lines if -analysis_range <= pos <= analysis_range]
    analysis_major = [pos for pos in major_lines if -analysis_range <= pos <= analysis_range]
    analysis_ruler = [pos for pos in ruler_major_ticks if -analysis_range <= pos <= analysis_range]
    
    info_text.append(f"Analysis in ±{analysis_range} unit range:")
    info_text.append(f"  Minor lines: {len(analysis_minor)}")
    info_text.append(f"  Major lines: {len(analysis_major)}")
    info_text.append(f"  Ruler ticks: {len(analysis_ruler)}")
    info_text.append(f"")
    
    # Calculate ratios
    if len(analysis_ruler) > 0:
        minor_to_ruler = len(analysis_minor) / len(analysis_ruler)
        major_to_ruler = len(analysis_major) / len(analysis_ruler)
        info_text.append(f"Ratios:")
        info_text.append(f"  Minor/Ruler = {minor_to_ruler:.2f}")
        info_text.append(f"  Major/Ruler = {major_to_ruler:.2f}")
        
        # Check for the reported 4:3 ratio
        user_ratio = 4.0/3.0  # ≈ 1.33
        if abs(minor_to_ruler - user_ratio) < 0.2:
            info_text.append(f"  ⚠️  CLOSE TO REPORTED 4:3 = {user_ratio:.2f}")
        
        info_text.append(f"")
        info_text.append(f"Expected pattern:")
        info_text.append(f"  8 minor lines between major ruler ticks")
        info_text.append(f"  1 major line per ruler tick (perfect alignment)")
    
    # Add the info text to the scene
    info_display = scene.addText("\n".join(info_text), QFont("Courier", 9))
    info_display.setPos(-190, -190)
    info_display.setDefaultTextColor(QColor("black"))
    info_display.setZValue(10)
    
    # Add a legend
    legend_text = [
        "LEGEND:",
        "Red dots (R) = Ruler major ticks",
        "Blue squares (G) = Major grid lines", 
        "Green dots = Minor grid lines (every 4th)",
        "Thick lines = Grid lines (Minor: thin, Major: normal, Super: thick)"
    ]
    legend_display = scene.addText("\n".join(legend_text), QFont("Arial", 10))
    legend_display.setPos(50, -190)
    legend_display.setDefaultTextColor(QColor("darkBlue"))
    legend_display.setZValue(10)
    
    print(f"\nDetailed position analysis (first 10 of each):")
    print(f"Ruler major ticks: {[round(pos, 1) for pos in ruler_major_ticks[:10]]}")
    print(f"Major grid lines:  {[round(pos, 1) for pos in major_lines[:10]]}")
    print(f"Minor grid lines:  {[round(pos, 1) for pos in minor_lines[:10]]}")
    
    # Check alignment
    print(f"\nAlignment check:")
    aligned_count = 0
    for ruler_pos in ruler_major_ticks:
        closest_major = min(major_lines, key=lambda x: abs(x - ruler_pos)) if major_lines else None
        if closest_major is not None:
            offset = abs(closest_major - ruler_pos)
            if offset < 0.001:
                aligned_count += 1
            print(f"  Ruler {ruler_pos:.1f} -> Major {closest_major:.1f} (offset: {offset:.6f})")
    
    print(f"Perfect alignments: {aligned_count}/{len(ruler_major_ticks)}")
    
    # Show the window
    view.show()
    
    # Set up a timer to keep the app running for a few seconds
    def close_window():
        print("\nVisual diagnostic complete. Check the window for the grid-ruler visualization.")
        print("The window shows:")
        print("- Red dots (R) mark where ruler ticks should be")
        print("- Blue squares (G) mark where major grid lines are")
        print("- Green dots mark some minor grid lines") 
        print("- If aligned correctly, red dots and blue squares should overlap")
        view.close()
        app.quit()
    
    # Keep window open for 30 seconds for inspection
    QTimer.singleShot(30000, close_window)
    
    # Return data for further analysis
    return {
        'minor_lines': len(analysis_minor),
        'major_lines': len(analysis_major), 
        'ruler_ticks': len(analysis_ruler),
        'aligned_count': aligned_count,
        'minor_to_ruler_ratio': len(analysis_minor) / len(analysis_ruler) if len(analysis_ruler) > 0 else 0,
        'major_to_ruler_ratio': len(analysis_major) / len(analysis_ruler) if len(analysis_ruler) > 0 else 0
    }

if __name__ == "__main__":
    try:
        result = create_visual_diagnostic()
        
        print(f"\n" + "="*60)
        print("VISUAL DIAGNOSTIC RESULTS:")
        print(f"Minor lines in analysis range: {result['minor_lines']}")
        print(f"Major lines in analysis range: {result['major_lines']}")
        print(f"Ruler ticks in analysis range: {result['ruler_ticks']}")
        print(f"Perfect alignments: {result['aligned_count']}")
        print(f"Minor-to-ruler ratio: {result['minor_to_ruler_ratio']:.2f}")
        print(f"Major-to-ruler ratio: {result['major_to_ruler_ratio']:.2f}")
        
        # Check if this matches the user's observation
        user_ratio = 4.0/3.0
        if abs(result['minor_to_ruler_ratio'] - user_ratio) < 0.2:
            print(f"⚠️  MATCHES USER REPORT: Ratio is close to 4:3 ({user_ratio:.2f})")
        else:
            print(f"ℹ️  Different from user report: Expected 4:3 = {user_ratio:.2f}, Got {result['minor_to_ruler_ratio']:.2f}")
        
        print("="*60)
        
        # Run the Qt event loop
        app.exec()
        
    except Exception as e:
        print(f"Error in visual diagnostic: {e}")
        import traceback
        traceback.print_exc()
