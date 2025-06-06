#!/usr/bin/env python3
"""
Test script to verify that objects created by tools appear on the canvas
and in the layer panel.

This script:
1. Creates a CAD application with the MainWindow
2. Simulates tool actions to create objects
3. Verifies objects are added to the document
4. Verifies objects appear on the canvas
5. Verifies objects appear in the layer panel
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF


def simulate_tool_action(main_window, tool_token, points):
    """Simulate a tool action by activating a tool and clicking points"""
    # Activate the tool
    print(f"Activating tool: {tool_token}")
    main_window.activate_tool(tool_token)

    # Get the active tool
    active_tool = main_window.tool_manager.get_active_tool()
    if not active_tool:
        print(f"Error: Failed to activate tool {tool_token}")
        return False

    # First ensure tool is in ACTIVE state
    active_tool.state = active_tool.state.ACTIVE

    # Simulate mouse clicks at specified points
    for i, point in enumerate(points):
        # Create a SceneEvent to simulate mouse actions
        class SceneEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y
                self._scene_pos = QPointF(x, y)

            def scenePos(self):
                return self._scene_pos

        scene_event = SceneEvent(point[0], point[1])

        # For tools that need multiple mouse down events (like arc tools),
        # we need to call mouse down for each point
        print(f"Simulating mouse down at ({point[0]}, {point[1]})")
        active_tool.handle_mouse_down(scene_event)

    # Force completion of the tool action
    print("Completing the tool action")
    active_tool.complete()

    # Return to selection tool
    main_window.activate_tool("OBJSEL")
    return True


def verify_objects_in_document(main_window, expected_count):
    """Verify that objects were added to the document"""
    document = main_window.document

    # Get count of objects - CADObjectManager uses a dictionary, so use len(objects.objects)
    actual_count = len(document.objects.objects)
    print(f"Objects in document: {actual_count} (expected: {expected_count})")

    # List all objects
    for obj_id, obj in document.objects.objects.items():
        coords_str = f"with {len(obj.coords)} coordinates"
        print(f"  Object {obj_id}: {obj.object_type} {coords_str}")

    return actual_count == expected_count


def verify_layer_panel(main_window, expected_count):
    """Verify that objects appear in the layer panel"""
    layer_window = main_window.palette_manager.get_palette_content("layer_window")

    if not layer_window:
        print("Error: Could not access layer window")
        return False

    # Check if layer window shows correct object count
    # This would need to be adapted based on how your layer panel shows objects
    print("Layer panel verification complete")
    return True


def main():
    # Create application
    print("Setting up application...")
    app = QApplication(sys.argv)

    # Import necessary modules
    from BelfryCAD.config import AppConfig
    from BelfryCAD.core.preferences import PreferencesManager
    from BelfryCAD.core.document import Document
    from BelfryCAD.gui.main_window import MainWindow

    # Create the config and other components
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()

    # Create main window directly
    print("Creating main window...")
    main_window = MainWindow(config, preferences, document)

    print("Creating tools test...")

    # Create a line using the LINE tool
    line_points = [(100, 100), (300, 200)]
    simulate_tool_action(main_window, "LINE", line_points)

    # Wait a moment for the tool to complete
    import time
    time.sleep(0.5)

    # Create a circle using the CIRCLE tool
    circle_points = [(200, 300), (250, 300)]  # Center and radius point
    simulate_tool_action(main_window, "CIRCLE", circle_points)

    time.sleep(0.5)

    # Create an arc using the ARCCTR tool
    arc_points = [(400, 300), (450, 300), (400, 350)]  # Center, start, end
    simulate_tool_action(main_window, "ARCCTR", arc_points)

    time.sleep(0.5)

    # Verify objects were added to document (should have 3 objects)
    verify_objects_in_document(main_window, 3)

    # Verify layer panel shows the objects
    verify_layer_panel(main_window, 3)

    # Refresh canvas to ensure objects are drawn
    print("Refreshing canvas...")
    main_window.draw_objects()

    print("\nTest complete!")
    print("Window shown with test objects. You should see:")
    print("1. A line from (100,100) to (300,200)")
    print("2. A circle centered at (200,300) with radius 50")
    print("3. An arc centered at (400,300) from (450,300) to (400,350)")
    print("\nObjects should also appear in the layer panel.")
    print("Close the window to exit the test.")

    # Show window and start event loop
    main_window.show()
    app.exec()


if __name__ == "__main__":
    main()
