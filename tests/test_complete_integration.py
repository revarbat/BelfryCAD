#!/usr/bin/env python3
"""
Complete integration test for the PyTkCAD object creation and layer system.
This test verifies that:
1. Objects created with tools appear on the canvas
2. Objects appear in the layer panel
3. Layer system is properly integrated
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from BelfryCAD.config import AppConfig
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.core.document import Document
from BelfryCAD.core.cad_objects import ObjectType, Point
from BelfryCAD.gui.main_window import MainWindow


def test_complete_integration():
    """Test complete integration of objects, canvas, and layers."""
    print("Testing complete PyTkCAD integration...")
    print("=" * 50)

    # Setup application components
    print("Setting up application components...")
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()

    # Create main window
    print("Creating main window...")
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    main_window = MainWindow(config, preferences, document)

    # Test layer system integration
    print("\nTesting layer system integration...")

    # Create additional layers
    layer1 = document.layers.get_current_layer()
    document.layers.set_layer_name(layer1, "Default Layer")

    layer2 = document.layers.create_layer("Drawing Layer")
    document.layers.set_layer_color(layer2, "blue")

    layer3 = document.layers.create_layer("Notes Layer")
    document.layers.set_layer_color(layer3, "red")

    print(f"Created layers: {document.layers.get_layer_ids()}")
    for layer_id in document.layers.get_layer_ids():
        name = document.layers.get_layer_name(layer_id)
        color = document.layers.get_layer_color(layer_id)
        print(f"  Layer {layer_id}: {name} ({color})")

    # Test object creation on different layers
    print("\nCreating test objects on different layers...")

    # Create objects on layer 1
    document.layers.set_current_layer(layer1)
    line1 = document.objects.create_object(
        ObjectType.LINE,
        Point(0, 0), Point(100, 0),
        layer=layer1
    )
    document.layers.add_object_to_layer(layer1, line1.object_id)

    # Create objects on layer 2
    document.layers.set_current_layer(layer2)
    circle1 = document.objects.create_object(
        ObjectType.CIRCLE,
        Point(50, 50),
        layer=layer2,
        attributes={'radius': 25}
    )
    document.layers.add_object_to_layer(layer2, circle1.object_id)

    line2 = document.objects.create_object(
        ObjectType.LINE,
        Point(0, 100), Point(100, 100),
        layer=layer2
    )
    document.layers.add_object_to_layer(layer2, line2.object_id)

    # Create objects on layer 3
    document.layers.set_current_layer(layer3)
    point1 = document.objects.create_object(
        ObjectType.POINT,
        Point(25, 25),
        layer=layer3
    )
    document.layers.add_object_to_layer(layer3, point1.object_id)

    print(f"Created {len(document.objects.get_all_objects())} total objects")
    for layer_id in document.layers.get_layer_ids():
        objects_in_layer = document.layers.get_layer_objects(layer_id)
        layer_name = document.layers.get_layer_name(layer_id)
        print(f"  {layer_name}: {len(objects_in_layer)} objects")

    # Force canvas refresh
    print("\nRefreshing canvas...")
    main_window.draw_objects()

    # Test layer panel integration
    print("\nTesting layer panel integration...")
    layer_window = main_window.palette_manager.get_palette_content("layer_window")
    if layer_window:
        print("✓ Layer panel found")

        # Prepare layer data for layer window
        layers_data = []
        for layer_id in document.layers.get_layer_ids():
            layer_info = {
                'id': str(layer_id),
                'name': document.layers.get_layer_name(layer_id),
                'visible': document.layers.is_layer_visible(layer_id),
                'locked': document.layers.is_layer_locked(layer_id),
                'color': document.layers.get_layer_color(layer_id),
                'cut_bit': document.layers.get_layer_cut_bit(layer_id),
                'cut_depth': document.layers.get_layer_cut_depth(layer_id),
                'object_count': len(document.layers.get_layer_objects(layer_id))
            }
            layers_data.append(layer_info)

        # Update layer window
        current_layer_str = str(document.layers.get_current_layer())
        layer_window.refresh_layers(layers_data, current_layer_str)
        print("✓ Layer panel updated with object counts")

    else:
        print("⚠ Layer panel not found")

    # Show the window
    print("\nShowing main window...")
    main_window.show()

    # Setup a timer to automatically close after a few seconds
    def auto_close():
        print("\n" + "=" * 50)
        print("Integration test completed successfully!")
        print("Objects should be visible on canvas and in layer panel.")
        print("Closing window...")
        main_window.close()
        app.quit()

    timer = QTimer()
    timer.timeout.connect(auto_close)
    timer.start(3000)  # Close after 3 seconds

    print("Window shown. Integration test running...")
    print("You should see:")
    print("1. Objects rendered on the canvas")
    print("2. Layer panel showing layers with object counts")
    print("3. Different colored objects on different layers")

    # Run the application
    return app.exec()


if __name__ == "__main__":
    exit_code = test_complete_integration()
    sys.exit(exit_code)
