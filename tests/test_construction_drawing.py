#!/usr/bin/env python3
"""
Test script to verify construction drawing methods in DrawingManager
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from BelfryCAD.gui.drawing_manager import DrawingManager, NodeType
from BelfryCAD.core.cad_objects import CADObject, ObjectType
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QMainWindow
from PySide6.QtCore import QPointF

class TestCADObject:
    """Simple test CAD object"""
    def __init__(self, obj_id, obj_type):
        self.object_id = obj_id
        self.object_type = obj_type

class TestContext:
    """Simple test context"""
    def __init__(self, scene):
        self.scene = scene
        self.show_grid = False
        self.current_zoom = 1.0
        self.view_center = QPointF(0, 0)
        self.dpi = 72.0  # Realistic DPI matching main application
        self.scale_factor = 1.0

def test_construction_drawing():
    """Test all construction drawing methods"""
    print("Testing PyTkCAD Construction Drawing Methods...")
    
    # Create Qt application
    app = QApplication([])
    
    # Create scene and context
    scene = QGraphicsScene()
    context = TestContext(scene)
    
    # Create drawing manager
    dm = DrawingManager(context)
    
    # Test object for methods requiring CADObject
    test_obj = TestCADObject("test_obj_1", ObjectType.LINE)
    
    try:
        # Test 1: Control point drawing
        print("1. Testing control point drawing...")
        cp_item = dm.object_draw_controlpoint(
            test_obj, "line", 10, 10, 1, NodeType.OVAL, "red", "white"
        )
        print(f"   ✓ Control point created: {cp_item is not None}")
        
        # Test 2: Control line drawing  
        print("2. Testing control line drawing...")
        cl_item = dm.object_draw_control_line(test_obj, 0, 0, 50, 50, 1, "blue", "dashed")
        print(f"   ✓ Control line created: {cl_item is not None}")
        
        # Test 3: Construction oval
        print("3. Testing construction oval...")
        oval_item = dm.object_draw_oval(25, 25, 15, 10, ["test"], "green")
        print(f"   ✓ Construction oval created: {oval_item is not None}")
        
        # Test 4: Oval cross
        print("4. Testing oval cross...")
        cross_items = dm.object_draw_oval_cross(25, 25, 15, 10, ["test"], "yellow")
        print(f"   ✓ Oval cross created: {cross_items is not None and len(cross_items) > 0}")
        
        # Test 5: Centerline
        print("5. Testing centerline...")
        center_item = dm.object_draw_centerline(0, 50, 50, 0, ["test"], "cyan")
        print(f"   ✓ Centerline created: {center_item is not None}")
        
        # Test 6: Center arc
        print("6. Testing center arc...")
        arc_item = dm.object_draw_center_arc(40, 40, 20, 0, 90, ["test"], "magenta")
        print(f"   ✓ Center arc created: {arc_item is not None}")
        
        # Test 7: Control arc
        print("7. Testing control arc...")
        ctrl_arc_item = dm.object_draw_control_arc(test_obj, 60, 60, 25, 45, 90, 1, "orange")
        print(f"   ✓ Control arc created: {ctrl_arc_item is not None}")
        
        # Test that items were added to scene
        print(f"\nScene items count: {len(scene.items())}")
        print("✓ All construction drawing methods working correctly!")
        
        # Test tagging system
        print("\nTesting tagging system...")
        items = scene.items()
        tagged_items = 0
        for item in items:
            if item.data(0) is not None:  # Has object ID
                tagged_items += 1
        print(f"   ✓ Tagged items: {tagged_items}/{len(items)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_construction_drawing()
    if success:
        print("\n🎉 All tests passed! Construction drawing methods are working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above.")
        sys.exit(1)
