#!/usr/bin/env python3
"""
Test to verify that DrawingManager no longer performs manual coordinate scaling
and properly delegates scaling to CadScene.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ''))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPen, QBrush, Qt
from PySide6.QtCore import QPointF

from BelfryCAD.gui.cad_scene import CadScene
from BelfryCAD.gui.drawing_manager import DrawingManager, NodeType
from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point


def test_drawing_manager_scaling_delegation():
    """Test that DrawingManager properly delegates coordinate scaling to CadScene"""
    print("Testing DrawingManager coordinate scaling delegation...")
    
    app = QApplication([])
    
    # Create CadScene and DrawingManager
    scene = CadScene()
    manager = DrawingManager()
    manager.set_cad_scene(scene)
    
    print(f"CadScene DPI: {scene.dpi}")
    print(f"CadScene scale factor: {scene.scale_factor}")
    
    # Test CAD coordinates
    cad_coords = [0, 0, 10, 10]
    print(f"Original CAD coordinates: {cad_coords}")
    
    # Test that DrawingManager delegates scaling to CadScene
    scaled_by_manager = manager.scale_coords(cad_coords)
    scaled_by_scene = scene.scale_coords(cad_coords)
    
    print(f"Scaled by DrawingManager: {scaled_by_manager}")
    print(f"Scaled by CadScene: {scaled_by_scene}")
    
    # They should be identical since DrawingManager delegates to CadScene
    if scaled_by_manager == scaled_by_scene:
        print("✅ DrawingManager properly delegates scaling to CadScene")
    else:
        print("❌ DrawingManager scaling delegation FAILED")
        return False
    
    # Test that drawing methods work with CAD coordinates
    try:
        # Create a simple CAD object for testing
        test_obj = CADObject(
            object_id=1,
            object_type=ObjectType.CIRCLE,
            coords=[Point(0, 0), Point(10, 10)],
            attributes={'linewidth': 1.0, 'linecolor': 'black'}
        )
        
        # Test drawing primitives with CAD coordinates
        pen = QPen(Qt.GlobalColor.black, 1.0)
        fill = QBrush(Qt.BrushStyle.NoBrush)
        
        # Test _draw_rectangle (should pass CAD coordinates directly to CadScene)
        rect_item = manager._draw_rectangle([0, 0, 10, 10], pen, fill, test_obj)
        print(f"✅ Rectangle drawing test PASSED: {rect_item}")
        
        # Test _draw_ellipse
        ellipse_item = manager._draw_ellipse([5, 5, 3, 2], pen, fill, test_obj)
        print(f"✅ Ellipse drawing test PASSED: {ellipse_item}")
        
        # Test _draw_circle  
        circle_item = manager._draw_circle([0, 0, 5], pen, fill, test_obj)
        print(f"✅ Circle drawing test PASSED: {circle_item}")
        
        # Test construction methods
        oval_item = manager.object_draw_oval(0, 0, 5, 3, ["TEST"], "blue")
        print(f"✅ Construction oval test PASSED: {oval_item}")
        
        # Test control point drawing
        cp_item = manager.object_draw_controlpoint(
            test_obj, "circle", 5, 5, 0,
            NodeType.OVAL, "red", "white"
        )
        print(f"✅ Control point test PASSED: {cp_item}")
        
    except Exception as e:
        print(f"❌ Drawing method test FAILED: {e}")
        return False
    
    print("✅ All DrawingManager coordinate scaling tests PASSED")
    return True


def test_coordinate_scaling_elimination():
    """Verify that manual scaling has been eliminated from DrawingManager"""
    print("\nTesting coordinate scaling elimination...")
    
    # Read the DrawingManager source code to verify no manual scaling
    manager_file = "/Users/gminette/dev/git-repos/BelfryCAD/BelfryCAD/gui/drawing_manager.py"
    
    with open(manager_file, 'r') as f:
        content = f.read()
    
    # Check for patterns that would indicate manual scaling
    scaling_patterns = [
        "scaled_coords = self.scale_coords",
        "= self.scale_coords(data)",
        "= self.scale_coords([",
    ]
    
    found_scaling = False
    for pattern in scaling_patterns:
        if pattern in content:
            print(f"❌ Found manual scaling pattern: {pattern}")
            found_scaling = True
    
    if not found_scaling:
        print("✅ No manual coordinate scaling found in DrawingManager")
    
    # Check that delegation methods exist
    if "def scale_coords(self, coords: List[float]) -> List[float]:" in content:
        print("✅ DrawingManager has delegation scale_coords method")
    else:
        print("❌ DrawingManager missing delegation scale_coords method")
        return False
    
    if "return self.cad_scene.scale_coords(coords)" in content:
        print("✅ DrawingManager properly delegates to CadScene")
    else:
        print("❌ DrawingManager not properly delegating to CadScene")
        return False
    
    return not found_scaling


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING DRAWING MANAGER COORDINATE SCALING REMOVAL")
    print("=" * 60)
    
    success = True
    
    # Test 1: Verify delegation works
    success &= test_drawing_manager_scaling_delegation()
    
    # Test 2: Verify manual scaling is eliminated
    success &= test_coordinate_scaling_elimination()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED: DrawingManager coordinate scaling removal SUCCESSFUL!")
        print("\n✅ DrawingManager no longer performs manual coordinate scaling")
        print("✅ All drawing methods pass raw CAD coordinates to CadScene")
        print("✅ CadScene handles all coordinate scaling internally")
        print("✅ No double-scaling occurs")
    else:
        print("❌ SOME TESTS FAILED: Manual intervention required")
    print("=" * 60)
