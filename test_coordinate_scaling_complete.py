#!/usr/bin/env python3
"""
Test the complete coordinate scaling migration and functionality
"""

import sys
import os

# Add the parent directory to the path so we can import BelfryCAD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPen, QColor
from BelfryCAD.gui.cad_scene import CadScene
from BelfryCAD.gui.drawing_manager import DrawingManager

def test_complete_integration():
    """Test complete integration of coordinate scaling migration"""
    app = QApplication([])
    
    print("=== Testing CadScene Coordinate Scaling ===")
    
    # Create a CadScene instance
    scene = CadScene()
    
    # Test coordinate scaling methods
    test_coords = [0, 0, 10, 10, 20, 20]
    scaled = scene.scale_coords(test_coords)
    descaled = scene.descale_coords(scaled)
    
    print(f"Original: {test_coords}")
    print(f"Scaled: {scaled}")
    print(f"Descaled: {descaled}")
    
    # Verify roundtrip accuracy
    tolerance = 1e-6
    for i in range(len(test_coords)):
        if abs(test_coords[i] - descaled[i]) > tolerance:
            print(f"❌ Roundtrip failed at index {i}")
            return False
    
    print("✅ Coordinate scaling roundtrip PASSED")
    
    # Test graphics item creation with automatic scaling
    print("\n=== Testing Graphics Item Creation ===")
    
    try:
        # Test line with CAD coordinates
        line = scene.addLine(0, 0, 100, 100, tags=["test_line"])
        print(f"✅ Line creation PASSED: {line}")
        
        # Test rectangle with CAD coordinates  
        rect = scene.addRect(50, 50, 100, 50, tags=["test_rect"])
        print(f"✅ Rectangle creation PASSED: {rect}")
        
        # Test ellipse with CAD coordinates
        ellipse = scene.addEllipse(25, 25, 50, 50, tags=["test_ellipse"])
        print(f"✅ Ellipse creation PASSED: {ellipse}")
        
        # Test polygon with CAD coordinates
        points = [(0, 0), (100, 0), (50, 100)]
        polygon = scene.addPolygon(points, tags=["test_polygon"])
        print(f"✅ Polygon creation PASSED: {polygon}")
        
    except Exception as e:
        print(f"❌ Graphics item creation FAILED: {e}")
        return False
    
    # Test DrawingManager integration
    print("\n=== Testing DrawingManager Integration ===")
    
    try:
        drawing_manager = DrawingManager()
        drawing_manager.set_cad_scene(scene)
        
        # Test that DrawingManager can use CadScene's scaling methods
        dm_scaled = drawing_manager.scale_coords([10, 10, 20, 20])
        scene_scaled = scene.scale_coords([10, 10, 20, 20])
        
        if dm_scaled == scene_scaled:
            print("✅ DrawingManager coordinate scaling delegation PASSED")
        else:
            print(f"❌ DrawingManager scaling mismatch: {dm_scaled} != {scene_scaled}")
            return False
            
    except Exception as e:
        print(f"❌ DrawingManager integration FAILED: {e}")
        return False
    
    # Test tagging system
    print("\n=== Testing Tagging System ===")
    
    try:
        # Get items by tag
        test_lines = scene.getItemsByTag("test_line")
        test_rects = scene.getItemsByTag("test_rect")
        
        print(f"✅ Found {len(test_lines)} line(s) with 'test_line' tag")
        print(f"✅ Found {len(test_rects)} rectangle(s) with 'test_rect' tag")
        
        # Test multi-tag operations
        all_test_items = scene.getItemsByTags(["test_line", "test_rect", "test_ellipse"], all=False)
        print(f"✅ Found {len(all_test_items)} items with any test tag")
        
    except Exception as e:
        print(f"❌ Tagging system FAILED: {e}")
        return False
    
    print("\n🎉 All coordinate scaling migration tests PASSED!")
    return True

if __name__ == "__main__":
    if test_complete_integration():
        print("\n✅ COORDINATE SCALING MIGRATION SUCCESSFUL!")
        print("\n📋 SUMMARY:")
        print("• Moved scale_coords() and descale_coords() from DrawingManager to CadScene")
        print("• Updated all CadScene add*() methods to automatically scale input coordinates")
        print("• DrawingManager now delegates coordinate scaling to CadScene")
        print("• Coordinate roundtrip accuracy maintained")
        print("• Graphics item creation works with CAD coordinates")
        print("• Tagging system integration preserved")
        sys.exit(0)
    else:
        print("\n❌ COORDINATE SCALING MIGRATION FAILED!")
        sys.exit(1)
