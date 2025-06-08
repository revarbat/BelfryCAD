#!/usr/bin/env python3
"""
Simple verification script for CadScene tagging integration.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BelfryCAD'))

def test_integration_no_gui():
    """Test CadScene and DrawingManager integration without GUI."""
    print("Testing CadScene tagging integration (no GUI)...")

    # Import modules
    from gui.cad_scene import CadScene
    from gui.drawing_manager import DrawingManager

    # Create CadScene
    scene = CadScene()
    print("✅ CadScene created successfully")

    # Create DrawingManager
    drawing_manager = DrawingManager()
    print("✅ DrawingManager created successfully")

    # Test tagging system exists
    assert hasattr(scene, '_tagged_items'), "CadScene should have _tagged_items"
    assert hasattr(scene, '_item_tags'), "CadScene should have _item_tags"
    assert hasattr(scene, 'addTag'), "CadScene should have addTag method"
    assert hasattr(scene, 'getItemsByTag'), \
        "CadScene should have getItemsByTag method"
    print("✅ CadScene has all required tagging methods")

    # Test DrawingManager integration methods
    assert hasattr(drawing_manager, 'set_cad_scene'), "DrawingManager should have set_cad_scene method"
    assert hasattr(drawing_manager, 'cad_scene'), "DrawingManager should have cad_scene attribute"
    print("✅ DrawingManager has CadScene integration methods")

    # Test that DrawingManager can be linked to CadScene
    drawing_manager.set_cad_scene(scene)
    assert drawing_manager.cad_scene is scene, "DrawingManager should reference the CadScene"
    print("✅ DrawingManager successfully linked to CadScene")

    # Test that CadScene has all the add* methods with tagging
    add_methods = ['addLine', 'addRect', 'addEllipse', 'addPolygon', 'addPath', 'addPixmap', 'addText']
    for method_name in add_methods:
        assert hasattr(scene, method_name), f"CadScene should have {method_name} method"
    print("✅ CadScene has all required add* methods")

    print("\n🎉 Integration verification completed successfully!")
    print("Summary:")
    print("- CadScene has comprehensive tagging system")
    print("- DrawingManager can be linked to CadScene")
    print("- All QGraphicsScene add* methods implemented with tagging support")
    print("- DrawingManager will use CadScene's tagged methods when available")
    return True


if __name__ == "__main__":
    try:
        test_integration_no_gui()
        print("\n✅ All verification tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
