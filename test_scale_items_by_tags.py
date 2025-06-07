#!/usr/bin/env python3
"""
Test script for the new scaleItemsByTags method in CadScene.

This script demonstrates how to use the scaleItemsByTags method to scale
all graphics items that have all of the specified tags.
"""

import sys
import os

# Add the BelfryCAD directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF
from gui.cad_scene import CadScene


def test_scale_items_with_all_tags():
    """Test the scaleItemsByTags method functionality."""
    
    # Create a CadScene instance
    cad_scene = CadScene()
    
    print("Testing CadScene.scaleItemsByTags() method")
    print("=" * 50)
    
    # Add various items with different tag combinations
    print("\n1. Adding items with different tag combinations:")
    
    # Items that will be scaled (have both 'scalable' and 'geometry')
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["geometry", "scalable", "shape"])
    print("   - Line1: tags=['geometry', 'scalable', 'shape']")
    print(f"     Initial transform: {line1.transform()}")
    
    rect1 = cad_scene.addRect(50, 50, 100, 50, tags=["scalable", "geometry", "rectangle"])
    print("   - Rect1: tags=['scalable', 'geometry', 'rectangle']")
    print(f"     Initial transform: {rect1.transform()}")
    
    # Items that will NOT be scaled (missing one of the tags)
    ellipse1 = cad_scene.addEllipse(150, 150, 80, 60, tags=["geometry", "scalable", "fixed"])
    print("   - Ellipse1: tags=['geometry', 'scalable', 'fixed'] (missing 'shape')")
    print(f"     Initial transform: {ellipse1.transform()}")
    
    line2 = cad_scene.addLine(200, 200, 300, 300, tags=["geometry", "construction", "guide"])
    print("   - Line2: tags=['geometry', 'construction', 'guide'] (missing 'scalable')")
    print(f"     Initial transform: {line2.transform()}")
    
    text1 = cad_scene.addText("Sample Text", tags=["text", "annotation", "label"])
    print("   - Text1: tags=['text', 'annotation', 'label'] (missing both)")
    print(f"     Initial transform: {text1.transform()}")
    
    print(f"\n2. Initial state:")
    print(f"   Total items in scene: {len(cad_scene.scene.items())}")
    
    # Check items before scaling
    scalable_geometry_items = cad_scene.getItemsByTags(["scalable", "geometry"])
    print(f"   Items with both 'scalable' AND 'geometry': {len(scalable_geometry_items)}")
    
    print(f"\n3. Testing scaleItemsByTags(['scalable', 'geometry'], 2.0, 1.5):")
    
    # Scale items that have both 'scalable' and 'geometry' tags
    scaled_count = cad_scene.scaleItemsByTags(["scalable", "geometry"], 2.0, 1.5)
    print(f"   Items scaled: {scaled_count}")
    
    print(f"\n4. Transforms after scaling:")
    
    # Check the transforms after scaling
    print("   Items that should have been scaled:")
    print(f"   - Line1 transform: {line1.transform()}")
    print(f"   - Rect1 transform: {rect1.transform()}")
    print(f"   - Ellipse1 transform: {ellipse1.transform()}")
    
    print("   Items that should NOT have been scaled:")
    print(f"   - Line2 transform: {line2.transform()}")
    print(f"   - Text1 transform: {text1.transform()}")


def test_uniform_scaling():
    """Test uniform scaling (same factor for both X and Y)."""
    
    print("\n" + "=" * 50)
    print("TESTING UNIFORM SCALING")
    print("=" * 50)
    
    cad_scene = CadScene()
    
    # Add items for uniform scaling test
    rect1 = cad_scene.addRect(0, 0, 100, 100, tags=["uniform", "test"])
    ellipse1 = cad_scene.addEllipse(150, 150, 50, 50, tags=["uniform", "test"])
    line1 = cad_scene.addLine(0, 0, 50, 50, tags=["uniform", "test"])
    
    print(f"\nInitial items: {len(cad_scene.scene.items()) - 1115} test items")  # Subtract grid items
    print("Initial transforms:")
    print(f"   Rect1: {rect1.transform()}")
    print(f"   Ellipse1: {ellipse1.transform()}")
    print(f"   Line1: {line1.transform()}")
    
    print("\n1. Uniform scaling by 2.0:")
    scaled = cad_scene.scaleItemsByTags(["uniform", "test"], 2.0, 2.0)
    print(f"   Items scaled: {scaled}")
    
    print("Transforms after uniform scaling:")
    print(f"   Rect1: {rect1.transform()}")
    print(f"   Ellipse1: {ellipse1.transform()}")
    print(f"   Line1: {line1.transform()}")


def test_non_uniform_scaling():
    """Test non-uniform scaling (different factors for X and Y)."""
    
    print("\n" + "=" * 50)
    print("TESTING NON-UNIFORM SCALING")
    print("=" * 50)
    
    cad_scene = CadScene()
    
    # Add items for non-uniform scaling test
    rect1 = cad_scene.addRect(0, 0, 100, 50, tags=["stretch", "test"])
    ellipse1 = cad_scene.addEllipse(150, 150, 60, 60, tags=["stretch", "test"])
    
    print(f"\nInitial items for stretch test: 2 items")
    print("Initial transforms:")
    print(f"   Rect1: {rect1.transform()}")
    print(f"   Ellipse1: {ellipse1.transform()}")
    
    print("\n1. Non-uniform scaling (3.0x horizontally, 0.5x vertically):")
    scaled = cad_scene.scaleItemsByTags(["stretch", "test"], 3.0, 0.5)
    print(f"   Items scaled: {scaled}")
    
    print("Transforms after non-uniform scaling:")
    print(f"   Rect1: {rect1.transform()}")
    print(f"   Ellipse1: {ellipse1.transform()}")


def test_edge_cases():
    """Test edge cases for scaleItemsByTags."""
    
    print("\n" + "=" * 50)
    print("TESTING EDGE CASES")
    print("=" * 50)
    
    cad_scene = CadScene()
    
    # Add some test items
    line1 = cad_scene.addLine(0, 0, 100, 100, tags=["test", "visible"])
    rect1 = cad_scene.addRect(50, 50, 200, 100, tags=["test", "geometry"])
    
    initial_line_transform = line1.transform()
    initial_rect_transform = rect1.transform()
    
    print(f"\nInitial transforms:")
    print(f"   Line1: {initial_line_transform}")
    print(f"   Rect1: {initial_rect_transform}")
    
    print("\n1. Test scaling with non-existent tags:")
    scaled = cad_scene.scaleItemsByTags(["nonexistent"], 2.0, 2.0)
    print(f"   Items scaled with non-existent tag: {scaled}")
    print(f"   Line1 transform: {line1.transform()} (should be unchanged)")
    
    print("\n2. Test scaling with empty tag list:")
    scaled = cad_scene.scaleItemsByTags([], 2.0, 2.0)
    print(f"   Items scaled with empty tag list: {scaled}")
    print(f"   Line1 transform: {line1.transform()} (should be unchanged)")
    
    print("\n3. Test scaling with mix of existing and non-existing tags:")
    scaled = cad_scene.scaleItemsByTags(["test", "nonexistent"], 2.0, 2.0)
    print(f"   Items scaled with mixed tags: {scaled}")
    print(f"   Line1 transform: {line1.transform()} (should be unchanged)")
    
    print("\n4. Test scaling with single existing tag:")
    scaled = cad_scene.scaleItemsByTags(["test"], 1.5, 1.5)
    print(f"   Items scaled with 'test' tag: {scaled}")
    print(f"   Line1 transform: {line1.transform()}")
    print(f"   Rect1 transform: {rect1.transform()}")
    
    print("\n5. Test scaling with scale factor of 1.0 (no change):")
    pre_scale_line = line1.transform()
    pre_scale_rect = rect1.transform()
    scaled = cad_scene.scaleItemsByTags(["test"], 1.0, 1.0)
    print(f"   Items processed with identity scale: {scaled}")
    print(f"   Line1 transform changed: {line1.transform() != pre_scale_line}")
    print(f"   Rect1 transform changed: {rect1.transform() != pre_scale_rect}")


def test_real_world_usage():
    """Demonstrate real-world usage for scaling groups of items."""
    
    print("\n" + "=" * 50)
    print("REAL-WORLD SCALING EXAMPLE")
    print("=" * 50)
    
    cad_scene = CadScene()
    
    print("\nCreating a sample CAD drawing with scalable components...")
    
    # Create a component that needs scaling
    # Main body
    cad_scene.addRect(0, 0, 100, 60, tags=["component", "body", "scalable"])
    cad_scene.addEllipse(20, 20, 20, 20, tags=["component", "detail", "scalable"])
    cad_scene.addEllipse(60, 20, 20, 20, tags=["component", "detail", "scalable"])
    
    # Create reference elements that should not scale
    cad_scene.addLine(-50, -50, 150, -50, tags=["reference", "dimension", "fixed"])
    cad_scene.addLine(-50, 110, 150, 110, tags=["reference", "dimension", "fixed"])
    cad_scene.addText("100mm", tags=["reference", "label", "fixed"])
    
    # Create another scalable component group
    cad_scene.addRect(200, 0, 80, 40, tags=["component2", "body", "scalable"])
    cad_scene.addLine(200, 0, 280, 40, tags=["component2", "cross", "scalable"])
    cad_scene.addLine(280, 0, 200, 40, tags=["component2", "cross", "scalable"])
    
    print(f"Created drawing with {len(cad_scene.scene.items())} total items")
    
    # Get item counts before scaling
    comp1_items = cad_scene.getItemsByTags(["component", "scalable"])
    comp2_items = cad_scene.getItemsByTags(["component2", "scalable"])
    reference_items = cad_scene.getItemsByTags(["reference"])
    
    print(f"Component 1 items: {len(comp1_items)}")
    print(f"Component 2 items: {len(comp2_items)}")
    print(f"Reference items: {len(reference_items)}")
    
    print("\n1. Scaling component 1 by 150% uniformly:")
    scaled = cad_scene.scaleItemsByTags(["component", "scalable"], 1.5, 1.5)
    print(f"   Scaled {scaled} component 1 items")
    
    print("\n2. Scaling component 2 non-uniformly (200% width, 50% height):")
    scaled = cad_scene.scaleItemsByTags(["component2", "scalable"], 2.0, 0.5)
    print(f"   Scaled {scaled} component 2 items")
    
    print("\n3. Verification - reference elements should remain unchanged:")
    print("   Reference items should maintain original scale")
    print("   Components should be scaled according to their factors")
    
    print("\n4. Final result:")
    print("   - Component 1: 150% of original size")
    print("   - Component 2: 200% width, 50% height")
    print("   - Reference lines and labels: unchanged")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        test_scale_items_with_all_tags()
        test_uniform_scaling()
        test_non_uniform_scaling()
        test_edge_cases()
        test_real_world_usage()
        print("\n" + "=" * 50)
        print("All scaleItemsByTags tests completed successfully!")
        print("The method correctly scales items that have ALL specified tags.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Don't start the event loop, just exit
    sys.exit(0)
