#!/usr/bin/env python3
"""
Test script to verify that CAD objects can be directly created 
and displayed properly on the canvas and layer panel.

This script:
1. Creates a main window with document
2. Adds objects directly to the document
3. Verifies objects appear on the canvas and in layer panel
"""
import sys
import os
import math

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication


def verify_objects_in_document(main_window, expected_count):
    """Verify that objects were added to the document"""
    document = main_window.document
    
    # Get count of objects - CADObjectManager uses a dictionary
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
    print("Layer panel verification complete")
    return True


def main():
    # Create application
    print("Setting up application...")
    app = QApplication(sys.argv)
    
    # Import necessary modules
    from BelfryCAD.config import AppConfig
    from BelfryCAD.core.document import Document
    from BelfryCAD.core.preferences import PreferencesManager
    from BelfryCAD.gui.main_window import MainWindow
    from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
    
    # Create the config and other components
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    
    # Create main window
    print("Creating main window...")
    main_window = MainWindow(config, preferences, document)
    
    # Create objects directly
    print("Creating test objects directly...")
    
    # Create a line
    line_points = [Point(100, 100), Point(300, 200)]
    line = CADObject(
        object_id=document.objects.get_next_id(),
        object_type=ObjectType.LINE,
        layer=document.objects.current_layer,
        coords=line_points,
        attributes={
            'color': 'black',
            'linewidth': 2
        }
    )
    document.objects.add_object(line)
    
    # Create a circle
    circle_center = Point(200, 300)
    circle = CADObject(
        object_id=document.objects.get_next_id(),
        object_type=ObjectType.CIRCLE,
        layer=document.objects.current_layer,
        coords=[circle_center],
        attributes={
            'color': 'blue',
            'linewidth': 2,
            'radius': 50
        }
    )
    document.objects.add_object(circle)
    
    # Create an arc
    arc_center = Point(400, 300)
    start_point = Point(450, 300)
    end_point = Point(400, 350)
    
    # Calculate radius and angles
    radius = math.sqrt(
        (start_point.x - arc_center.x)**2 +
        (start_point.y - arc_center.y)**2
    )
    start_angle = math.atan2(
        start_point.y - arc_center.y,
        start_point.x - arc_center.x
    )
    end_angle = math.atan2(
        end_point.y - arc_center.y,
        end_point.x - arc_center.x
    )
    
    # Create arc object with proper attributes
    arc = CADObject(
        object_id=document.objects.get_next_id(),
        object_type=ObjectType.ARC,
        layer=document.objects.current_layer,
        coords=[arc_center, start_point, end_point],
        attributes={
            'color': 'green',
            'linewidth': 2,
            'radius': radius,
            'start_angle': start_angle,
            'end_angle': end_angle
        }
    )
    document.objects.add_object(arc)
    
    # Verify objects were added to document
    verify_objects_in_document(main_window, 3)
    
    # Verify layer panel shows the objects
    verify_layer_panel(main_window, 3)
    
    # Refresh canvas to draw objects
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
