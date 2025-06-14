#!/usr/bin/env python3
"""
Test script to verify CadScene functionality after refactoring
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

# Add the project root to Python path
sys.path.insert(0, '/Users/gminette/dev/git-repos/BelfryCAD')

from BelfryCAD.gui.cad_scene import CadScene
from BelfryCAD.core.document import Document


def test_cad_scene():
    """Test basic CadScene functionality."""
    app = QApplication([])

    # Create a test document
    document = Document()

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("CadScene Test")

    # Create CadScene
    cad_scene = CadScene(document=document, parent=window)
    window.setCentralWidget(cad_scene)

    # Test that all components are accessible
    scene = cad_scene
    canvas = cad_scene.get_canvas()
    drawing_manager = cad_scene.get_drawing_manager()
    ruler_manager = cad_scene.get_ruler_manager()
    drawing_context = cad_scene.get_drawing_context()

    print("✅ CadScene created successfully")
    print(f"✅ Scene: {scene}")
    print(f"✅ Canvas: {canvas}")
    print(f"✅ Drawing Manager: {drawing_manager}")
    print(f"✅ Ruler Manager: {ruler_manager}")
    print(f"✅ Drawing Context: {drawing_context}")

    # Test signal connections
    def test_mouse_position(x, y):
        print(f"✅ Mouse position signal: {x}, {y}")

    def test_scale_change(scale):
        print(f"✅ Scale changed signal: {scale}")

    cad_scene.mouse_position_changed.connect(test_mouse_position)
    cad_scene.scale_changed.connect(test_scale_change)

    # Test method calls
    cad_scene.set_dpi(96.0)
    cad_scene.set_scale_factor(1.5)
    cad_scene.set_grid_visibility(True)
    cad_scene.set_origin_visibility(True)

    print("✅ All CadScene methods callable")
    print("✅ CadScene refactoring test completed successfully!")

    return True


if __name__ == "__main__":
    success = test_cad_scene()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
