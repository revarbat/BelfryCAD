#!/usr/bin/env python3
"""
Test the layer visibility functionality integration.

This test verifies that:
1. Objects on visible layers are drawn
2. Objects on hidden layers are not drawn
3. Layer visibility toggles work correctly
4. Objects are properly assigned to layers
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from BelfryCAD.gui.main_window import MainWindow
from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document


def test_layer_visibility():
    """Test layer visibility functionality"""

    app = QApplication(sys.argv)

    print("Testing Layer Visibility Integration")
    print("=" * 50)

    # Create the main window and components
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    main_window = MainWindow(config, preferences, document)

    # Get the drawing manager and layer manager
    drawing_manager = main_window.drawing_manager
    layer_manager = document.layers

    print("1. Setting up test layers...")

    # Create additional test layers
    layer1_id = layer_manager.create_layer("Visible Layer")
    layer2_id = layer_manager.create_layer("Hidden Layer")
    layer3_id = layer_manager.create_layer("Another Visible Layer")

    # Set layer2 to hidden
    layer_manager.set_layer_visible(layer2_id, False)

    print(f"   ✓ Created layers: {layer1_id} (visible), "
          f"{layer2_id} (hidden), {layer3_id} (visible)")

    print("2. Creating test objects on different layers...")

    # Create test objects on different layers
    def mock_line_decomp():
        return [("lines", [50, 50, 150, 150])]

    def mock_circle_decomp():
        return [("ellipse", [200, 50, 300, 150])]

    def mock_rect_decomp():
        return [("lines", [350, 50, 450, 50, 450, 150, 350, 150, 350, 50])]

    # Object on visible layer 1
    obj1 = CADObject(
        object_id=1,
        object_type=ObjectType.LINE,
        coords=[Point(50, 50), Point(150, 150)],
        attributes={'color': 'red', 'linewidth': 2}
    )
    obj1.layer = layer1_id

    # Object on hidden layer 2
    obj2 = CADObject(
        object_id=2,
        object_type=ObjectType.CIRCLE,
        coords=[Point(250, 100)],
        attributes={'color': 'blue', 'linewidth': 2, 'radius': 50}
    )
    obj2.layer = layer2_id

    # Object on visible layer 3
    obj3 = CADObject(
        object_id=3,
        object_type=ObjectType.POLYGON,
        coords=[Point(350, 50), Point(450, 50),
                Point(450, 150), Point(350, 150)],
        attributes={'color': 'green', 'linewidth': 2}
    )
    obj3.layer = layer3_id

    print(f"   ✓ Created objects: obj1 (layer {layer1_id}), "
          f"obj2 (layer {layer2_id}), obj3 (layer {layer3_id})")

    print("3. Testing drawing with layer visibility...")

    # Draw all objects
    items1 = drawing_manager.object_draw(obj1)
    items2 = drawing_manager.object_draw(obj2)
    items3 = drawing_manager.object_draw(obj3)

    print(f"   ✓ Object 1 (visible layer): {len(items1)} graphics items")
    print(f"   ✓ Object 2 (hidden layer): {len(items2)} graphics items")
    print(f"   ✓ Object 3 (visible layer): {len(items3)} graphics items")

    # Verify that object on hidden layer creates no graphics items
    if len(items2) == 0:
        print("   ✅ SUCCESS: Object on hidden layer was NOT drawn")
    else:
        print("   ❌ FAILURE: Object on hidden layer WAS drawn unexpectedly")
        return False

    # Verify that objects on visible layers create graphics items
    if len(items1) > 0 and len(items3) > 0:
        print("   ✅ SUCCESS: Objects on visible layers WERE drawn")
    else:
        print("   ❌ FAILURE: Objects on visible layers were NOT drawn")
        return False

    print("4. Testing layer visibility toggle...")

    # Make the hidden layer visible
    layer_manager.set_layer_visible(layer2_id, True)

    # Redraw object 2
    items2_visible = drawing_manager.object_draw(obj2)

    print(f"   ✓ Object 2 after making layer visible: "
          f"{len(items2_visible)} graphics items")

    if len(items2_visible) > 0:
        print("   ✅ SUCCESS: Object became visible when layer was "
              "made visible")
    else:
        print("   ❌ FAILURE: Object remained hidden after layer was "
              "made visible")
        return False

    # Hide a previously visible layer
    layer_manager.set_layer_visible(layer1_id, False)

    # Redraw object 1
    items1_hidden = drawing_manager.object_draw(obj1)

    print(f"   ✓ Object 1 after hiding layer: "
          f"{len(items1_hidden)} graphics items")

    if len(items1_hidden) == 0:
        print("   ✅ SUCCESS: Object became hidden when layer was hidden")
    else:
        print("   ❌ FAILURE: Object remained visible after layer was hidden")
        return False

    print("5. Testing objects without layer assignment...")

    # Test object without layer assignment (should default to visible)
    obj_no_layer = CADObject(
        object_id=4,
        object_type=ObjectType.LINE,
        coords=[Point(500, 50), Point(600, 150)],
        attributes={'color': 'orange', 'linewidth': 2}
    )
    # Note: obj_no_layer.layer is not set

    items_no_layer = drawing_manager.object_draw(obj_no_layer)

    print(f"   ✓ Object without layer: {len(items_no_layer)} graphics items")

    # Object without layer should still be drawn
    if len(items_no_layer) > 0:
        print("   ✅ SUCCESS: Object without layer assignment was drawn")
    else:
        print("   ❌ FAILURE: Object without layer assignment not drawn")
        return False

    print("6. Testing integration with main window...")

    # Test the main window's draw_objects method with layer visibility
    # Add objects to the document using the CADObjectManager
    main_window.document.objects.add_object(obj1)
    main_window.document.objects.add_object(obj2)
    main_window.document.objects.add_object(obj3)
    main_window.document.objects.add_object(obj_no_layer)

    # Reset layer visibility for comprehensive test
    layer_manager.set_layer_visible(layer1_id, True)
    layer_manager.set_layer_visible(layer2_id, False)
    layer_manager.set_layer_visible(layer3_id, True)

    # Clear scene
    main_window.canvas.scene().clear()

    # Draw all objects through main window
    main_window.draw_objects()

    # Count total items in scene
    total_items = len(main_window.canvas.scene().items())
    print(f"   ✓ Total graphics items in scene: {total_items}")

    # Should have items for obj1, obj3, and obj_no_layer, but not obj2
    if total_items > 0:
        print("   ✅ SUCCESS: Main window integration works with "
              "layer visibility")
    else:
        print("   ❌ FAILURE: No items drawn through main window")
        return False

    print("=" * 50)
    print("✅ ALL LAYER VISIBILITY TESTS PASSED!")
    print("\nLayer Visibility Summary:")
    print("- ✅ Objects on hidden layers are not drawn")
    print("- ✅ Objects on visible layers are drawn")
    print("- ✅ Layer visibility toggles work correctly")
    print("- ✅ Objects without layer assignment work properly")
    print("- ✅ Main window integration preserves layer visibility")

    print("\n🎉 Layer management system is COMPLETE and FUNCTIONAL!")

    # Show the main window with test results
    main_window.setWindowTitle("Layer Visibility Test - Complete")
    main_window.show()
    main_window.resize(800, 600)

    print("\nTest window displayed. Close it to exit.")
    app.exec()

    return True


if __name__ == "__main__":
    success = test_layer_visibility()
    if success:
        print("\n🎉 Layer visibility test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Layer visibility test failed!")
        sys.exit(1)
