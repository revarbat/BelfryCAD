#!/usr/bin/env python3
"""
Test script to verify ControlDatum precision updates work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from src.BelfryCAD.gui.views.graphics_items.control_points import ControlDatum
from src.BelfryCAD.gui.widgets.cad_scene import CadScene
from src.BelfryCAD.gui.views.graphics_items.caditems.circle_center_radius_cad_item import CircleCenterRadiusCadItem


def test_control_datum_precision_update():
    """Test that ControlDatum updates its precision correctly."""
    print("Testing ControlDatum precision update...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a ControlDatum with initial precision
    datum = ControlDatum(
        setter=lambda x: None,
        prefix="R",
        precision=3
    )
    
    # Test initial format string
    expected_format = "{:.3f}"
    print(f"  Initial format: '{datum.format_string}' (expected '{expected_format}')")
    assert datum.format_string == expected_format, f"Expected '{expected_format}', got '{datum.format_string}'"
    
    # Test updating precision
    datum.update_precision(5)
    expected_format = "{:.5f}"
    print(f"  Updated format: '{datum.format_string}' (expected '{expected_format}')")
    assert datum.format_string == expected_format, f"Expected '{expected_format}', got '{datum.format_string}'"
    
    print("  ✓ ControlDatum precision update test passed")


def test_cad_item_control_datum_precision():
    """Test that CAD items update ControlDatum precision correctly."""
    print("Testing CAD item ControlDatum precision...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a scene with precision
    scene = CadScene(precision=3)
    
    # Create a CAD item
    cad_item = CircleCenterRadiusCadItem()
    scene.addItem(cad_item)
    
    # Create controls (this will create ControlDatums)
    cad_item.createControls()
    
    # Check that ControlDatums have the correct precision
    for control_item in cad_item._control_point_items:
        if hasattr(control_item, 'format_string'):
            print(f"  ControlDatum format: '{control_item.format_string}'")
            # Should have 3 decimal places based on scene precision
            assert "{:.3f}" in control_item.format_string, f"Expected format with 3 decimals, got '{control_item.format_string}'"
    
    # Update scene precision
    scene.set_precision(5)
    
    # Update CAD item ControlDatums
    cad_item.update_control_datums_precision(5)
    
    # Check that ControlDatums have updated precision
    for control_item in cad_item._control_point_items:
        if hasattr(control_item, 'format_string'):
            print(f"  Updated ControlDatum format: '{control_item.format_string}'")
            # Should have 5 decimal places
            assert "{:.5f}" in control_item.format_string, f"Expected format with 5 decimals, got '{control_item.format_string}'"
    
    print("  ✓ CAD item ControlDatum precision test passed")


def test_scene_control_datum_precision_update():
    """Test that scene updates all ControlDatums' precision correctly."""
    print("Testing scene ControlDatum precision update...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a scene with precision
    scene = CadScene(precision=3)
    
    # Create multiple CAD items
    cad_items = []
    for i in range(3):
        cad_item = CircleCenterRadiusCadItem()
        scene.addItem(cad_item)
        cad_item.createControls()
        cad_items.append(cad_item)
    
    # Verify initial precision
    for cad_item in cad_items:
        for control_item in cad_item._control_point_items:
            if hasattr(control_item, 'format_string'):
                assert "{:.3f}" in control_item.format_string, f"Expected format with 3 decimals, got '{control_item.format_string}'"
    
    # Update scene precision
    scene.update_all_control_datums_precision(7)
    
    # Verify updated precision
    for cad_item in cad_items:
        for control_item in cad_item._control_point_items:
            if hasattr(control_item, 'format_string'):
                print(f"  Updated ControlDatum format: '{control_item.format_string}'")
                assert "{:.7f}" in control_item.format_string, f"Expected format with 7 decimals, got '{control_item.format_string}'"
    
    print("  ✓ Scene ControlDatum precision update test passed")


def test_control_datum_show_precision():
    """Test that ControlDatums get correct precision when shown."""
    print("Testing ControlDatum show precision...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a scene with precision
    scene = CadScene(precision=4)
    
    # Create a CAD item
    cad_item = CircleCenterRadiusCadItem()
    scene.addItem(cad_item)
    
    # Create controls
    cad_item.createControls()
    
    # Simulate showing controls (this should update precision)
    cad_item.showControls()
    
    # Check that ControlDatums have the scene's precision
    for control_item in cad_item._control_point_items:
        if hasattr(control_item, 'format_string'):
            print(f"  ControlDatum format after show: '{control_item.format_string}'")
            assert "{:.4f}" in control_item.format_string, f"Expected format with 4 decimals, got '{control_item.format_string}'"
    
    print("  ✓ ControlDatum show precision test passed")


def main():
    """Run all ControlDatum precision tests."""
    print("Running ControlDatum precision update tests...")
    print()
    
    try:
        test_control_datum_precision_update()
        print()
        
        test_cad_item_control_datum_precision()
        print()
        
        test_scene_control_datum_precision_update()
        print()
        
        test_control_datum_show_precision()
        print()
        
        print("All ControlDatum precision update tests passed! ✓")
        return 0
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 