#!/usr/bin/env python3
"""
Test script specifically for Arc3PointTool (ARC3PT) to verify it works correctly.
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF


def simulate_arc3pt_tool(main_window, points):
    """Simulate the ARC3PT tool with given points"""
    # Activate the ARC3PT tool
    print(f"Activating tool: ARC3PT")
    main_window.activate_tool("ARC3PT")

    # Get the active tool
    active_tool = main_window.tool_manager.get_active_tool()
    if not active_tool:
        print(f"Error: Failed to activate tool ARC3PT")
        return False

    # Ensure tool is in ACTIVE state
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

        print(f"Simulating mouse down at ({point[0]}, {point[1]})")
        active_tool.handle_mouse_down(scene_event)

    # Force completion of the tool action
    print("Completing the tool action")
    active_tool.complete()

    # Return to selection tool
    main_window.activate_tool("OBJSEL")
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

    # Create main window
    print("Creating main window...")
    main_window = MainWindow(config, preferences, document)

    print("Creating Arc3PT test...")

    # Test 1: Create an arc using ARC3PT tool - quarter circle
    arc_points = [(100, 100), (150, 150), (200, 100)]  # Start, middle, end
    simulate_arc3pt_tool(main_window, arc_points)

    time.sleep(0.5)

    # Test 2: Create another arc using ARC3PT tool - different shape
    arc_points2 = [(300, 200), (350, 150), (400, 200)]  # Start, middle, end
    simulate_arc3pt_tool(main_window, arc_points2)

    time.sleep(0.5)

    # Verify objects were added to document
    document = main_window.document
    actual_count = len(document.objects.objects)
    expected_count = 2

    print(f"Objects in document: {actual_count} (expected: {expected_count})")
    for i, (obj_id, obj) in enumerate(document.objects.objects.items(), 1):
        print(f"  Object {i}: {obj.object_type} with {len(obj.coords)} coordinates")
        if hasattr(obj, 'attributes'):
            if 'radius' in obj.attributes:
                print(f"    Radius: {obj.attributes['radius']:.2f}")
            if 'start_angle' in obj.attributes:
                print(f"    Start angle: {obj.attributes['start_angle']:.3f} rad")
            if 'end_angle' in obj.attributes:
                print(f"    End angle: {obj.attributes['end_angle']:.3f} rad")

    # Refresh canvas to ensure objects are drawn
    print("Refreshing canvas...")
    main_window.draw_objects()

    print("\nTest complete!")
    print("Window shown with test arcs. You should see:")
    print("1. An arc from (100,100) through (150,150) to (200,100)")
    print("2. An arc from (300,200) through (350,150) to (400,200)")
    print("\nBoth should display as curved arcs, not straight lines.")
    print("Close the window to exit the test.")

    # Show window and start event loop
    main_window.show()
    app.exec()


if __name__ == "__main__":
    main()
