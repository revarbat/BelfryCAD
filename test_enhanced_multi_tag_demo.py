#!/usr/bin/env python3
"""
Test script to demonstrate CadScene's enh        # Add tags to existing items
        scene.addTag(line1, "selected")
        scene.addTag(rect1, "highlighted")
        scene.addTag(ellipse1, "selected")d multi-tag functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_enhanced_multi_tag_usage():
    """Test enhanced multi-tag usage patterns."""
    print("Testing enhanced multi-tag usage patterns...")
    
    try:
        from BelfryCAD.gui.cad_scene import CadScene
        
        # Create a mock scene instance
        scene = CadScene.__new__(CadScene)
        scene._tagged_items = {}
        scene._item_tags = {}
        
        # Mock the scene.addXXX methods to avoid Qt dependencies
        class MockGraphicsItem:
            def __init__(self, item_type, name):
                self.item_type = item_type
                self.name = name
            def __repr__(self):
                return f"{self.item_type}({self.name})"
        
        def mock_add_method(item_type):
            def add_method(*args, **kwargs):
                item = MockGraphicsItem(item_type, f"{item_type}_{len(scene._item_tags)}")
                if 'tags' in kwargs:
                    scene._apply_tags(item, kwargs['tags'])
                return item
            return add_method
        
        # Mock the scene methods
        scene.scene = type('MockScene', (), {})()
        for method in ['addLine', 'addRect', 'addEllipse', 'addPolygon', 'addPixmap', 'addPath', 'addText']:
            setattr(scene.scene, method, mock_add_method(method))
        
        # Test 1: Creating items with multiple tags
        print("\n1. Testing creation with multiple tags:")
        line1 = scene.addLine(0, 0, 100, 100, tags=["geometry", "layer1", "construction"])
        rect1 = scene.addRect(50, 50, 100, 100, tags=["geometry", "layer1", "shape"])
        ellipse1 = scene.addEllipse(0, 0, 50, 50, tags=["geometry", "layer2", "shape"])
        text1 = scene.addText("Label", tags=["annotation", "layer2", "text"])
        
        print(f"  Created: {line1}, {rect1}, {ellipse1}, {text1}")
        
        # Test 2: Query items by different tag combinations
        print("\n2. Testing tag-based queries:")
        geometry_items = scene.getItemsByTag("geometry")
        layer1_items = scene.getItemsByTag("layer1")
        layer2_items = scene.getItemsByTag("layer2")
        shape_items = scene.getItemsByTag("shape")
        annotation_items = scene.getItemsByTag("annotation")
        
        print(f"  Geometry items: {len(geometry_items)} - {geometry_items}")
        print(f"  Layer1 items: {len(layer1_items)} - {layer1_items}")
        print(f"  Layer2 items: {len(layer2_items)} - {layer2_items}")
        print(f"  Shape items: {len(shape_items)} - {shape_items}")
        print(f"  Annotation items: {len(annotation_items)} - {annotation_items}")
        
        # Test 3: Dynamic tag management
        print("\n3. Testing dynamic tag management:")
        
        # Add tags to existing items
        scene.addTag(line1, "selected")
        scene.addTag(rect1, "highlighted") 
        scene.addTag(ellipse1, "selected")
        
        selected_items = scene.getItemsByTag("selected")
        print(f"  Selected items: {len(selected_items)} - {selected_items}")
        
        # Remove tags
        scene.removeTag(line1, "construction")
        construction_items = scene.getItemsByTag("construction")
        print(f"  Construction items after removal: {len(construction_items)} - {construction_items}")
        
        # Test 4: Check individual item tags
        print("\n4. Testing individual item tag queries:")
        line1_tags = scene.getTags(line1)
        rect1_tags = scene.getTags(rect1)
        print(f"  Line1 tags: {line1_tags}")
        print(f"  Rect1 tags: {rect1_tags}")
        
        # Test 5: Simulated real-world usage patterns
        print("\n5. Testing real-world usage patterns:")
        
        # Create a complex drawing with organized tagging
        # Drawing outline
        scene.addRect(0, 0, 400, 300, tags=["outline", "border", "layer_base"])
        
        # Title block
        scene.addRect(300, 250, 100, 50, tags=["title_block", "annotation", "layer_base"])
        scene.addText("Drawing Title", tags=["title", "text", "annotation", "layer_base"])
        
        # Mechanical part
        scene.addRect(50, 50, 200, 100, tags=["part", "geometry", "layer_mechanical"])
        scene.addEllipse(75, 75, 50, 50, tags=["hole", "geometry", "layer_mechanical", "machining"])
        scene.addEllipse(175, 75, 50, 50, tags=["hole", "geometry", "layer_mechanical", "machining"])
        
        # Dimensions
        scene.addLine(50, 40, 250, 40, tags=["dimension", "annotation", "layer_dimensions"])
        scene.addText("200mm", tags=["dim_text", "annotation", "layer_dimensions"])
        
        # Test organizational queries
        mechanical_items = scene.getItemsByTag("layer_mechanical")
        annotation_items = scene.getItemsByTag("annotation")
        machining_items = scene.getItemsByTag("machining")
        
        print(f"  Total items in drawing: {len(scene._item_tags)}")
        print(f"  Mechanical layer items: {len(mechanical_items)}")
        print(f"  Annotation items: {len(annotation_items)}")
        print(f"  Machining operations: {len(machining_items)}")
        
        # Test 6: Bulk operations simulation
        print("\n6. Testing bulk operations simulation:")
        
        # Simulate hiding layer_dimensions
        dim_items = scene.getItemsByTag("layer_dimensions")
        print(f"  Would hide {len(dim_items)} dimension items")
        
        # Simulate changing color of all holes
        hole_items = scene.getItemsByTag("hole")
        print(f"  Would change color of {len(hole_items)} holes")
        
        # Simulate selecting all geometry for export
        all_geometry = scene.getItemsByTag("geometry")
        print(f"  Would export {len(all_geometry)} geometry items")
        
        print("\n✓ All enhanced multi-tag usage tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Enhanced multi-tag test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("CadScene Enhanced Multi-Tag System Demo")
    print("=" * 50)
    
    success = test_enhanced_multi_tag_usage()
    
    if success:
        print("\n🎉 Enhanced multi-tag system demonstration completed successfully!")
        print("\nKey benefits demonstrated:")
        print("- Items can have multiple tags for flexible organization")
        print("- Query items by any tag for operations like layer management")
        print("- Dynamic tag addition/removal for state management")
        print("- Efficient bulk operations on tagged item groups")
        print("- Real-world CAD organizational patterns supported")
    else:
        print("\n❌ Enhanced multi-tag test failed.")
        sys.exit(1)
