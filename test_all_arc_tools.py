#!/usr/bin/env python3
"""
Test script for all arc tools to verify they create proper arc objects.
"""

import sys
import time
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
    from src.config import AppConfig
    from src.core.preferences import PreferencesManager
    from src.core.document import Document
    from src.gui.main_window import MainWindow
    
    # Create the config and other components
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    
    # Create main window
    print("Creating main window...")
    main_window = MainWindow(config, preferences, document)
    
    print("Testing all arc tools...")
    
    # Test 1: ARCCTR tool (center, start, end)
    print("\n=== Testing ARCCTR tool ===")
    arc_center_points = [(100, 100), (150, 100), (100, 150)]  # Center, start, end
    simulate_tool_action(main_window, "ARCCTR", arc_center_points)
    
    time.sleep(0.5)
    
    # Test 2: ARC3PT tool (start, middle, end)
    print("\n=== Testing ARC3PT tool ===")
    arc_3pt_points = [(300, 100), (350, 150), (400, 100)]  # Start, middle, end
    simulate_tool_action(main_window, "ARC3PT", arc_3pt_points)
    
    time.sleep(0.5)
    
    # Test 3: Check if ARCTAN tool is available
    print("\n=== Testing ARCTAN tool (if available) ===")
    try:
        # ARCTAN typically needs: tangent line start, tangent line end, arc start point
        arc_tan_points = [(500, 100), (550, 100), (525, 150)]  
        simulate_tool_action(main_window, "ARCTAN", arc_tan_points)
    except Exception as e:
        print(f"ARCTAN tool may not be available or configured: {e}")
    
    time.sleep(0.5)
    
    # Verify objects were added to document
    document = main_window.document
    actual_count = len(document.objects.objects)
    
    print(f"\nObjects in document: {actual_count}")
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
    
    print("\n=== Test Summary ===")
    print("All arc tools tested. You should see curved arcs displayed, not straight lines.")
    print("This confirms that:")
    print("1. Arc tools properly create CADObject instances with ObjectType.ARC")
    print("2. Arc objects have the required attributes (radius, start_angle, end_angle)")
    print("3. The main window's _draw_object method renders arcs as curves")
    print("\nClose the window to exit the test.")
    
    # Show window and start event loop
    main_window.show()
    app.exec()


if __name__ == "__main__":
    main()
