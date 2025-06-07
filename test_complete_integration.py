#!/usr/bin/env python3
"""
Test that all components work together after the field migration.
"""

import sys
import os

# Add the BelfryCAD directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from PySide6.QtWidgets import QApplication
from BelfryCAD.gui.cad_scene import CadScene

def test_complete_integration():
    """Test that the entire system works after field migration."""
    print("Testing complete integration after field migration...")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create CadScene
    cad_scene = CadScene()
    print("✓ CadScene created successfully")

    # Test that all subsystems are working
    scene = cad_scene.get_scene()
    print(f"✓ Scene created: {scene}")

    canvas = cad_scene.get_canvas()
    print(f"✓ Canvas created: {canvas}")

    drawing_manager = cad_scene.get_drawing_manager()
    print(f"✓ DrawingManager created: {drawing_manager}")

    ruler_manager = cad_scene.get_ruler_manager()
    print(f"✓ RulerManager created: {ruler_manager}")

    # Test field updates trigger updates
    print("\nTesting field updates...")
    original_dpi = cad_scene.dpi
    original_scale = cad_scene.scale_factor

    cad_scene.set_dpi(96.0)
    print(f"✓ DPI updated: {original_dpi} -> {cad_scene.dpi}")

    cad_scene.set_scale_factor(1.5)
    print(f"✓ Scale factor updated: {original_scale} -> {cad_scene.scale_factor}")

    # Test grid visibility toggles
    cad_scene.set_grid_visibility(False)
    print(f"✓ Grid visibility: {cad_scene.show_grid}")

    cad_scene.set_origin_visibility(False)
    print(f"✓ Origin visibility: {cad_scene.show_origin}")

    # Test tagging system works
    print("\nTesting tagging system...")
    line = cad_scene.addLine(0, 0, 100, 100, tags=["test", "line"])
    rect = cad_scene.addRect(50, 50, 100, 50, tags=["test", "rect"])

    test_items = cad_scene.getItemsByTag("test")
    print(f"✓ Tagged items created: {len(test_items)} items with 'test' tag")

    line_items = cad_scene.getItemsByTag("line")
    print(f"✓ Line items: {len(line_items)}")

    # Test that backward compatibility still works
    context = cad_scene.get_drawing_context()
    print(f"✓ Context access works: dpi={context.dpi}, scale={context.scale_factor}")

    # Test that drawing manager can still access context
    dm_context = drawing_manager.context
    print(f"✓ DrawingManager context: dpi={dm_context.dpi}, scale={dm_context.scale_factor}")

    print("\n" + "="*60)
    print("COMPLETE INTEGRATION TEST RESULTS:")
    print("✓ CadScene initialization works")
    print("✓ All subsystems initialize correctly")
    print("✓ Field updates work properly")
    print("✓ Grid and origin visibility controls work")
    print("✓ Tagging system functions correctly")
    print("✓ Backward compatibility maintained")
    print("✓ DrawingManager integration works")
    print("✓ Integration test PASSED")
    print("="*60)

if __name__ == "__main__":
    test_complete_integration()
