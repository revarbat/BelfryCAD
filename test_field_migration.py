#!/usr/bin/env python3
"""
Test that DrawingContext fields have been successfully migrated to CadScene.
"""

import sys
import os

# Add the BelfryCAD directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from PySide6.QtWidgets import QApplication
from BelfryCAD.gui.cad_scene import CadScene

def test_field_migration():
    """Test that all DrawingContext fields are now accessible in CadScene."""
    print("Testing DrawingContext field migration...")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create CadScene
    cad_scene = CadScene()
    print("✓ CadScene created")

    # Test direct field access
    print(f"✓ dpi: {cad_scene.dpi}")
    print(f"✓ scale_factor: {cad_scene.scale_factor}")
    print(f"✓ show_grid: {cad_scene.show_grid}")
    print(f"✓ show_origin: {cad_scene.show_origin}")
    print(f"✓ grid_color: {cad_scene.grid_color}")
    print(f"✓ origin_color_x: {cad_scene.origin_color_x}")
    print(f"✓ origin_color_y: {cad_scene.origin_color_y}")

    # Test field modifications
    cad_scene.dpi = 96.0
    cad_scene.scale_factor = 2.0
    cad_scene.show_grid = False
    cad_scene.show_origin = False
    print("✓ Field modifications work")

    # Test backward compatibility - context should reflect our changes
    context = cad_scene.get_drawing_context()
    print(f"✓ Context dpi: {context.dpi}")
    print(f"✓ Context scale_factor: {context.scale_factor}")
    print(f"✓ Context show_grid: {context.show_grid}")
    print(f"✓ Context show_origin: {context.show_origin}")

    # Verify the context reflects our changes
    assert context.dpi == 96.0, f"Expected dpi=96.0, got {context.dpi}"
    assert context.scale_factor == 2.0, f"Expected scale_factor=2.0, got {context.scale_factor}"
    assert context.show_grid == False, f"Expected show_grid=False, got {context.show_grid}"
    assert context.show_origin == False, f"Expected show_origin=False, got {context.show_origin}"
    print("✓ Backward compatibility context works correctly")

    # Test drawing manager context access
    drawing_manager = cad_scene.get_drawing_manager()
    print(f"✓ DrawingManager context dpi: {drawing_manager.context.dpi}")
    print(f"✓ DrawingManager context scale_factor: {drawing_manager.context.scale_factor}")

    assert drawing_manager.context.dpi == 96.0, "DrawingManager context dpi mismatch"
    assert drawing_manager.context.scale_factor == 2.0, "DrawingManager context scale_factor mismatch"
    print("✓ DrawingManager context integration works")

    print("\n" + "="*60)
    print("FIELD MIGRATION TEST RESULTS:")
    print("✓ All DrawingContext fields successfully moved to CadScene")
    print("✓ Direct field access works")
    print("✓ Field modifications work")
    print("✓ Backward compatibility maintained")
    print("✓ DrawingManager integration works")
    print("✓ Test PASSED")
    print("="*60)

if __name__ == "__main__":
    test_field_migration()
