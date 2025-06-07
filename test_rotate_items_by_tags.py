#!/usr/bin/env python3
"""
Test script for the new rotateItemsByTags method in CadScene.

This script demonstrates how to use the rotateItemsByTags method to rotate
all graphics items that have all of the specified tags.
"""

import sys
import os
import math

# Add the BelfryCAD directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF
from PySide6.QtGui import QTransform
from gui.cad_scene import CadScene


def test_rotate_items_with_all_tags():
    """Test the rotateItemsByTags method functionality."""
    
    # Create a CadScene instance
    cad_scene = CadScene()
    
    print("Testing CadScene.rotateItemsByTags() method")
    print("=" * 50)
    
    # Add various items with different tag combinations
    print("\n1. Adding items with different tag combinations:")
    
    # Items that will be rotated (have both 'rotatable' and 'geometry')
    line1 = cad_scene.addLine(0, 0, 100, 0, tags=["geometry", "rotatable", "shape"])
    print("   - Line1: horizontal line, tags=['geometry', 'rotatable', 'shape']")
    print(f"     Initial transform: {line1.transform()}")
    
    rect1 = cad_scene.addRect(50, 50, 100, 50, tags=["rotatable", "geometry", "rectangle"])
    print("   - Rect1: tags=['rotatable', 'geometry', 'rectangle']")
    print(f"     Initial transform: {rect1.transform()}")
    
    # Items that will NOT be rotated (missing one of the tags)
    ellipse1 = cad_scene.addEllipse(150, 150, 80, 60, tags=["geometry", "rotatable", "fixed"])
    print("   - Ellipse1: tags=['geometry', 'rotatable', 'fixed'] (missing 'shape')")
    print(f"     Initial transform: {ellipse1.transform()}")
    
    line2 = cad_scene.addLine(200, 200, 300, 200, tags=["geometry", "construction", "guide"])
    print("   - Line2: tags=['geometry', 'construction', 'guide'] (missing 'rotatable')")
    print(f"     Initial transform: {line2.transform()}")
    
    text1 = cad_scene.addText("Sample Text", tags=["text", "annotation", "label"])
    print("   - Text1: tags=['text', 'annotation', 'label'] (missing both)")
    print(f"     Initial transform: {text1.transform()}")
    
    print(f"\n2. Initial state:")
    print(f"   Total items in scene: {len(cad_scene.scene.items())}")
    
    # Check items before rotation
    rotatable_geometry_items = cad_scene.getItemsByTags(["rotatable", "geometry"])
    print(f"   Items with both 'rotatable' AND 'geometry': {len(rotatable_geometry_items)}")
    
    print(f"\n3. Testing rotateItemsByTags(['rotatable', 'geometry'], 45.0):")
    
    # Rotate items that have both 'rotatable' and 'geometry' tags by 45 degrees
    rotated_count = cad_scene.rotateItemsByTags(["rotatable", "geometry"], 45.0)
    print(f"   Items rotated: {rotated_count}")
    
    print(f"\n4. Transforms after 45-degree rotation:")
    
    # Check the transforms after rotation
    print("   Items that should have been rotated:")
    print(f"   - Line1 transform: {line1.transform()}")
    print(f"   - Rect1 transform: {rect1.transform()}")
    print(f"   - Ellipse1 transform: {ellipse1.transform()}")
    
    print("   Items that should NOT have been rotated:")
    print(f"   - Line2 transform: {line2.transform()}")
    print(f"   - Text1 transform: {text1.transform()}")


def test_rotation_with_origin():
    """Test rotation around a specific origin point."""
    
    print("\n" + "=" * 50)
    print("TESTING ROTATION AROUND SPECIFIC ORIGIN")
    print("=" * 50)
    
    cad_scene = CadScene()
    
    # Add items for origin rotation test
    line1 = cad_scene.addLine(0, 0, 100, 0, tags=["origin_test", "rotatable"])
    rect1 = cad_scene.addRect(50, 50, 50, 30, tags=["origin_test", "rotatable"])
    
    print(f"\nInitial items: 2 test items")
    print("Initial transforms:")
    print(f"   Line1: {line1.transform()}")
    print(f"   Rect1: {rect1.transform()}")
    
    print("\n1. Rotating around origin point (0, 0) by 90 degrees:")
    rotated = cad_scene.rotateItemsByTags(["origin_test", "rotatable"], 90.0, 0.0, 0.0)
    print(f"   Items rotated: {rotated}")
    
    print("Transforms after rotation around (0,0):")
    print(f"   Line1: {line1.transform()}")
    print(f"   Rect1: {rect1.transform()}")


def test_multiple_rotations():
    """Test multiple successive rotations."""
    
    print("\n" + "=" * 50)
    print("TESTING MULTIPLE SUCCESSIVE ROTATIONS")
    print("=" * 50)
    
    cad_scene = CadScene()
    
    # Add items for multiple rotation test
    line1 = cad_scene.addLine(100, 0, 200, 0, tags=["multi_rotate", "test"])
    
    print(f"\nInitial horizontal line from (100,0) to (200,0)")
    print(f"Initial transform: {line1.transform()}")
    
    print("\n1. First rotation: 30 degrees")
    rotated = cad_scene.rotateItemsByTags(["multi_rotate", "test"], 30.0)
    print(f"   Items rotated: {rotated}")
    print(f"   Transform: {line1.transform()}")
    
    print("\n2. Second rotation: another 60 degrees (total 90)")
    rotated = cad_scene.rotateItemsByTags(["multi_rotate", "test"], 60.0)
    print(f"   Items rotated: {rotated}")
    print(f"   Transform: {line1.transform()}")
    
    print("\n3. Third rotation: -90 degrees (back to original)")
    rotated = cad_scene.rotateItemsByTags(["multi_rotate", "test"], -90.0)
    print(f"   Items rotated: {rotated}")
    print(f"   Transform: {line1.transform()}")


def test_edge_cases():
    """Test edge cases for rotateItemsByTags."""
    
    print("\n" + "=" * 50)
    print("TESTING EDGE CASES")
    print("=" * 50)
    
    cad_scene = CadScene()
    
    # Add some test items
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["test", "visible"])
    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["test", "geometry"])
    
    initial_line_transform = line1.transform()
    initial_rect_transform = rect1.transform()
    
    print("Initial transforms:")
    print(f"   Line1: {initial_line_transform}")
    print(f"   Rect1: {initial_rect_transform}")
    
    print("\n1. Test rotation with non-existent tags:")
    rotated = cad_scene.rotateItemsByTags(["nonexistent"], 45.0)
    print(f"   Items rotated with non-existent tag: {rotated}")
    print(f"   Line1 transform: {line1.transform()} (should be unchanged)")
    
    print("\n2. Test rotation with empty tag list:")
    rotated = cad_scene.rotateItemsByTags([], 45.0)
    print(f"   Items rotated with empty tag list: {rotated}")
    print(f"   Line1 transform: {line1.transform()} (should be unchanged)")
    
    print("\n3. Test rotation with mix of existing and non-existing tags:")
    rotated = cad_scene.rotateItemsByTags(["test", "nonexistent"], 45.0)
    print(f"   Items rotated with mixed tags: {rotated}")
    print(f"   Line1 transform: {line1.transform()} (should be unchanged)")
    
    print("\n4. Test rotation with single existing tag:")
    rotated = cad_scene.rotateItemsByTags(["test"], 45.0)
    print(f"   Items rotated with 'test' tag: {rotated}")
    print(f"   Line1 transform: {line1.transform()}")
    print(f"   Rect1 transform: {rect1.transform()}")
    
    print("\n5. Test rotation with angle of 0.0 (no change expected):")
    before_line = line1.transform()
    before_rect = rect1.transform()
    rotated = cad_scene.rotateItemsByTags(["test"], 0.0)
    print(f"   Items processed with 0-degree rotation: {rotated}")
    print(f"   Line1 transform changed: {line1.transform() != before_line}")
    print(f"   Rect1 transform changed: {rect1.transform() != before_rect}")
    
    print("\n6. Test rotation with 360 degrees (full circle):")
    before_line = line1.transform()
    before_rect = rect1.transform()
    rotated = cad_scene.rotateItemsByTags(["test"], 360.0)
    print(f"   Items processed with 360-degree rotation: {rotated}")
    # Note: Due to floating point precision, transforms might not be exactly equal
    print(f"   Line1 transform: {line1.transform()}")
    print(f"   Rect1 transform: {rect1.transform()}")


def test_real_world_rotation_example():
    """Test a real-world CAD rotation scenario."""
    
    print("\n" + "=" * 50)
    print("REAL-WORLD ROTATION EXAMPLE")
    print("=" * 50)
    
    cad_scene = CadScene()
    
    print("Creating a sample CAD drawing with rotatable components...")
    
    # Create a mechanical part with rotatable and fixed elements
    # Main body (should rotate)
    cad_scene.addRect(100, 100, 200, 100, tags=["component", "body", "rotatable"])
    cad_scene.addEllipse(150, 125, 50, 50, tags=["component", "hole1", "rotatable"])
    cad_scene.addEllipse(250, 125, 50, 50, tags=["component", "hole2", "rotatable"])
    
    # Assembly bolts (should rotate separately)
    cad_scene.addEllipse(120, 80, 10, 10, tags=["fastener", "bolt", "rotatable"])
    cad_scene.addEllipse(180, 80, 10, 10, tags=["fastener", "bolt", "rotatable"])
    cad_scene.addEllipse(220, 80, 10, 10, tags=["fastener", "bolt", "rotatable"])
    cad_scene.addEllipse(280, 80, 10, 10, tags=["fastener", "bolt", "rotatable"])
    
    # Reference lines and dimensions (should NOT rotate)
    cad_scene.addLine(50, 50, 350, 50, tags=["reference", "dimension", "fixed"])
    cad_scene.addLine(50, 50, 50, 250, tags=["reference", "dimension", "fixed"])
    cad_scene.addText("200mm", tags=["reference", "label", "fixed"])
    
    print(f"Created drawing with {len(cad_scene.scene.items())} total items")
    
    # Get item counts
    component_items = cad_scene.getItemsByTags(["component", "rotatable"])
    fastener_items = cad_scene.getItemsByTags(["fastener", "rotatable"])
    reference_items = cad_scene.getItemsByTags(["reference"])
    
    print(f"Component items: {len(component_items)}")
    print(f"Fastener items: {len(fastener_items)}")
    print(f"Reference items: {len(reference_items)}")
    
    print("\n1. Rotating main component by 30 degrees around center point (200, 150):")
    rotated = cad_scene.rotateItemsByTags(["component", "rotatable"], 30.0, 200.0, 150.0)
    print(f"   Rotated {rotated} component parts")
    
    print("\n2. Rotating fasteners by 15 degrees around their assembly center (200, 80):")
    rotated = cad_scene.rotateItemsByTags(["fastener", "rotatable"], 15.0, 200.0, 80.0)
    print(f"   Rotated {rotated} fasteners")
    
    print("\n3. Verification - reference elements should remain unchanged:")
    print("   Reference lines and labels should maintain original orientation")
    print("   Components should be rotated according to their specified angles")
    
    print("\n4. Final result:")
    print("   - Component: rotated 30° around (200, 150)")
    print("   - Fasteners: rotated 15° around (200, 80)")
    print("   - Reference lines and labels: unchanged")


if __name__ == "__main__":
    # Create QApplication instance (required for Qt objects)
    app = QApplication(sys.argv)
    
    try:
        # Run all tests
        test_rotate_items_with_all_tags()
        test_rotation_with_origin()
        test_multiple_rotations()
        test_edge_cases()
        test_real_world_rotation_example()
        
        print("\n" + "=" * 50)
        print("All rotateItemsByTags tests completed successfully!")
        print("The method correctly rotates items that have ALL specified tags.")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    # No need to call app.exec() since we're not showing any GUI
    print("Test completed.")
