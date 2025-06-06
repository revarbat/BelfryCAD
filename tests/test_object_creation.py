#!/usr/bin/env python3
"""
Test script to verify that CAD objects are being created and rendered properly.
This can be used to debug the object creation and rendering pipeline.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from BelfryCAD.core.cad_objects import CADObject, ObjectType, Point
from BelfryCAD.core.document import Document
from BelfryCAD.core.preferences import PreferencesManager
from BelfryCAD.config import AppConfig
from BelfryCAD.gui.main_window import MainWindow

def test_object_creation():
    """Test creating CAD objects and verify they appear in the document and canvas."""

    app = QApplication(sys.argv)

    # Create required dependencies
    print("Setting up application components...")
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()

    # Create main window
    print("Creating main window...")
    window = MainWindow(config, preferences, document)

    # Create test objects
    print("Creating test objects...")

    # Create a line
    line_obj = CADObject(
        object_id=document.objects.get_next_id(),
        object_type=ObjectType.LINE,
        coords=[Point(10, 10), Point(100, 100)],
        attributes={'color': 'blue', 'linewidth': 2}
    )

    # Create a circle
    circle_obj = CADObject(
        object_id=document.objects.get_next_id(),
        object_type=ObjectType.CIRCLE,
        coords=[Point(150, 150)],
        attributes={'radius': 50, 'color': 'red', 'linewidth': 1}
    )

    # Add objects to document
    print("Adding objects to document...")
    document.objects.add_object(line_obj)
    document.objects.add_object(circle_obj)

    # Force canvas refresh
    print("Refreshing canvas...")
    window.canvas.update()

    # Check if objects are in the document
    objects = document.objects.get_all_objects()
    print(f"Objects in document: {len(objects)}")
    for i, obj in enumerate(objects):
        print(f"  Object {i+1}: {obj.object_type} with {len(obj.coords)} coordinates")

    # Show the window
    window.show()
    print("Window shown. You should see a line and circle on the canvas.")
    print("Close the window to exit the test.")

    return app.exec()

if __name__ == "__main__":
    sys.exit(test_object_creation())
