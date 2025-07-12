#!/usr/bin/env python3
"""
Test script to verify control point exclusion functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

from ..src.BelfryCAD.gui.views.graphics_items.caditems.line_cad_item import LineCadItem
from ..src.BelfryCAD.gui.views.graphics_items.caditems.polyline_cad_item import PolylineCadItem
from ..src.BelfryCAD.gui.views.graphics_items.caditems.circle_3points_cad_item import Circle3PointsCadItem
from ..src.BelfryCAD.gui.views.graphics_items.control_points import ControlPoint
from ..src.BelfryCAD.gui.snaps_system import SnapsSystem
from ..src.BelfryCAD.gui.views.widgets.cad_scene import CadScene
from ..src.BelfryCAD.gui.grid_info import GridInfo

def test_line_cad_item_exclusion():
    """Test control point exclusion for LineCadItem."""
    print("Testing LineCadItem control point exclusion...")
    
    # Create a line item
    line = LineCadItem(QPointF(0, 0), QPointF(10, 0))
    
    # Create control points
    control_points = line.createControls()
    
    # Test without exclusion
    all_cps = line.getControlPoints()
    print(f"  All control points: {len(all_cps)} points")
    assert len(all_cps) == 3, f"Expected 3 control points, got {len(all_cps)}"
    
    # Test with exclusion of start point
    excluded_cps = line.getControlPoints(exclude_cps=[control_points[0]])  # Exclude start point
    print(f"  Excluding start point: {len(excluded_cps)} points")
    assert len(excluded_cps) == 2, f"Expected 2 control points, got {len(excluded_cps)}"
    
    # Test with exclusion of end point
    excluded_cps = line.getControlPoints(exclude_cps=[control_points[1]])  # Exclude end point
    print(f"  Excluding end point: {len(excluded_cps)} points")
    assert len(excluded_cps) == 2, f"Expected 2 control points, got {len(excluded_cps)}"
    
    # Test with exclusion of midpoint
    excluded_cps = line.getControlPoints(exclude_cps=[control_points[2]])  # Exclude midpoint
    print(f"  Excluding midpoint: {len(excluded_cps)} points")
    assert len(excluded_cps) == 2, f"Expected 2 control points, got {len(excluded_cps)}"
    
    # Test with exclusion of multiple points
    excluded_cps = line.getControlPoints(exclude_cps=[control_points[0], control_points[1]])  # Exclude start and end
    print(f"  Excluding start and end: {len(excluded_cps)} points")
    assert len(excluded_cps) == 1, f"Expected 1 control point, got {len(excluded_cps)}"
    
    print("  ✓ LineCadItem exclusion test passed")

def test_polyline_cad_item_exclusion():
    """Test control point exclusion for PolylineCadItem."""
    print("Testing PolylineCadItem control point exclusion...")
    
    # Create a polyline item
    points = [QPointF(0, 0), QPointF(5, 5), QPointF(10, 0)]
    polyline = PolylineCadItem(points)
    
    # Create control points
    control_points = polyline.createControls()
    
    # Test without exclusion
    all_cps = polyline.getControlPoints()
    print(f"  All control points: {len(all_cps)} points")
    assert len(all_cps) == 3, f"Expected 3 control points, got {len(all_cps)}"
    
    # Test with exclusion of first point
    excluded_cps = polyline.getControlPoints(exclude_cps=[control_points[0]])
    print(f"  Excluding first point: {len(excluded_cps)} points")
    assert len(excluded_cps) == 2, f"Expected 2 control points, got {len(excluded_cps)}"
    
    # Test with exclusion of multiple points
    excluded_cps = polyline.getControlPoints(exclude_cps=[control_points[0], control_points[2]])
    print(f"  Excluding first and last: {len(excluded_cps)} points")
    assert len(excluded_cps) == 1, f"Expected 1 control point, got {len(excluded_cps)}"
    
    print("  ✓ PolylineCadItem exclusion test passed")

def test_circle_3points_cad_item_exclusion():
    """Test control point exclusion for Circle3PointsCadItem."""
    print("Testing Circle3PointsCadItem control point exclusion...")
    
    # Create a circle item
    circle = Circle3PointsCadItem(QPointF(0, 1), QPointF(1, 0), QPointF(0, -1))
    
    # Create control points
    control_points = circle.createControls()
    
    # Test without exclusion
    all_cps = circle.getControlPoints()
    print(f"  All control points: {len(all_cps)} points")
    assert len(all_cps) == 4, f"Expected 4 control points, got {len(all_cps)}"  # 3 points + center
    
    # Test with exclusion of first point
    excluded_cps = circle.getControlPoints(exclude_cps=[control_points[0]])
    print(f"  Excluding first point: {len(excluded_cps)} points")
    assert len(excluded_cps) == 3, f"Expected 3 control points, got {len(excluded_cps)}"
    
    # Test with exclusion of center point
    excluded_cps = circle.getControlPoints(exclude_cps=[control_points[3]])  # Center point
    print(f"  Excluding center point: {len(excluded_cps)} points")
    assert len(excluded_cps) == 3, f"Expected 3 control points, got {len(excluded_cps)}"
    
    print("  ✓ Circle3PointsCadItem exclusion test passed")

def test_snaps_system_integration():
    """Test that the snaps system correctly uses the exclusion parameter."""
    print("Testing snaps system integration...")
    
    # Create a scene and snaps system
    scene = CadScene()
    grid_info = GridInfo()
    snaps_system = SnapsSystem(scene, grid_info)
    
    # Create a line item and add it to the scene
    line = LineCadItem(QPointF(0, 0), QPointF(10, 0))
    scene.addItem(line)
    
    # Create control points and add them to the scene
    control_points = line.createControls()
    for cp in control_points:
        scene.addItem(cp)
    
    # Test snapping without exclusion
    mouse_pos = QPointF(0.5, 0.5)  # Very close to the start point
    snap_point = snaps_system.get_snap_point(mouse_pos)
    print(f"  Snap point without exclusion: {snap_point}")
    
    # Test snapping with exclusion of start point
    snap_point_excluded = snaps_system.get_snap_point(mouse_pos, exclude_cps=[control_points[0]])
    print(f"  Snap point with start point excluded: {snap_point_excluded}")
    
    # Debug: check what control points are available
    all_cps = line.getControlPoints()
    excluded_cps = line.getControlPoints(exclude_cps=[control_points[0]])
    print(f"  Available control points: {len(all_cps)}")
    print(f"  Available control points after exclusion: {len(excluded_cps)}")
    
    # The excluded snap point should be different (likely the end point or midpoint)
    # But only if there are other control points available
    if len(excluded_cps) > 0:
        assert snap_point != snap_point_excluded, "Snap points should be different when excluding control points"
    else:
        print("  Note: No other control points available after exclusion")
    
    print("  ✓ Snaps system integration test passed")

def main():
    """Run all tests."""
    print("Testing control point exclusion functionality...")
    print("=" * 50)
    
    # Create QApplication for Qt functionality
    app = QApplication([])
    
    try:
        test_line_cad_item_exclusion()
        test_polyline_cad_item_exclusion()
        test_circle_3points_cad_item_exclusion()
        test_snaps_system_integration()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! Control point exclusion is working correctly.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 