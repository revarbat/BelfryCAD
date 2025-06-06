#!/usr/bin/env python3
"""
Demonstration of DPI scaling effects on construction drawing
Shows how DPI affects the size and positioning of construction elements
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from BelfryCAD.gui.drawing_manager import DrawingManager, NodeType
from BelfryCAD.core.cad_objects import CADObject, ObjectType
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QMainWindow
from PySide6.QtCore import QPointF, QRectF

class TestCADObject:
    """Simple test CAD object"""
    def __init__(self, obj_id, obj_type):
        self.object_id = obj_id
        self.object_type = obj_type

class TestContext:
    """Test context with configurable DPI"""
    def __init__(self, scene, dpi, scale_factor):
        self.scene = scene
        self.show_grid = False
        self.current_zoom = 1.0
        self.view_center = QPointF(0, 0)
        self.dpi = dpi
        self.scale_factor = scale_factor

def test_dpi_scaling():
    """Test construction drawing with different DPI values"""
    print("DPI Scaling Demonstration for Construction Drawing")
    print("=" * 60)
    
    # Create Qt application
    app = QApplication([])
    
    # Test with different DPI values
    dpi_values = [1.0, 72.0, 96.0, 100.0]
    
    for dpi in dpi_values:
        print(f"\nTesting with DPI = {dpi}")
        print("-" * 30)
        
        # Create scene and context
        scene = QGraphicsScene()
        context = TestContext(scene, dpi, 1.0)
        
        # Create drawing manager
        dm = DrawingManager(context)
        
        # Test object
        test_obj = TestCADObject("test_obj", ObjectType.LINE)
        
        # Draw a control point at CAD coordinate (10, 10)
        cad_x, cad_y = 10.0, 10.0
        cp_item = dm.object_draw_controlpoint(
            test_obj, "line", cad_x, cad_y, 1, NodeType.OVAL, "red", "white"
        )
        
        # Get the actual Qt scene position
        if cp_item:
            bounds = cp_item.boundingRect()
            scene_pos = cp_item.pos()
            center_x = scene_pos.x() + bounds.center().x()
            center_y = scene_pos.y() + bounds.center().y()
            
            print(f"CAD coordinates: ({cad_x}, {cad_y})")
            print(f"Qt scene coordinates: ({center_x:.1f}, {center_y:.1f})")
            print(f"Expected Qt coordinates: ({cad_x * dpi:.1f}, {-cad_y * dpi:.1f})")
            
            # Verify coordinate scaling
            expected_x = cad_x * dpi
            expected_y = -cad_y * dpi  # Y-axis flip for CAD convention
            
            if abs(center_x - expected_x) < 1.0 and abs(center_y - expected_y) < 1.0:
                print("✓ Coordinate scaling is correct")
            else:
                print("✗ Coordinate scaling error")
        
        # Draw a control line from (0,0) to (20,20)
        line_item = dm.object_draw_control_line(test_obj, 0, 0, 20, 20, 1, "blue", "solid")
        
        if line_item:
            line_bounds = line_item.boundingRect()
            print(f"Line bounding box: {line_bounds.width():.1f} x {line_bounds.height():.1f}")
            expected_size = 20 * dpi * 1.414  # Diagonal length
            print(f"Expected diagonal: ~{expected_size:.1f}")
        
        print(f"Total scene items: {len(scene.items())}")

def main():
    """Main function"""
    test_dpi_scaling()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("- DPI = 1.0: Construction elements are tiny (1 pixel per unit)")
    print("- DPI = 72.0: Standard application scaling (72 pixels per unit)")
    print("- DPI = 96.0: High DPI scaling (96 pixels per unit)")
    print("- DPI = 100.0: Test scaling for easy calculations")
    print("\nRecommendation: Use DPI = 72.0 for realistic construction element sizes")

if __name__ == "__main__":
    main()
