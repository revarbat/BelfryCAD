#!/usr/bin/env python3
"""
Test script to verify precision preferences are working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from src.BelfryCAD.gui.grid_info import GridInfo, GridUnits
from src.BelfryCAD.gui.views.graphics_items.control_points import ControlDatum
from src.BelfryCAD.gui.widgets.cad_scene import CadScene
from src.BelfryCAD.gui.panes.config_pane import ConfigPane


def test_grid_info_precision():
    """Test that GridInfo uses the correct precision."""
    print("Testing GridInfo precision...")
    
    # Test with different precision values
    for precision in [1, 3, 5]:
        grid_info = GridInfo(GridUnits.INCHES_DECIMAL, decimal_places=precision)
        
        # Test formatting
        test_value = 1.23456789
        formatted = grid_info.format_label(test_value)
        
        # Check that the formatted string has the correct number of decimal places
        if '.' in formatted:
            decimal_part = formatted.split('.')[1]
            actual_precision = len(decimal_part)
            print(f"  Precision {precision}: {formatted} (expected ~{precision} decimals)")
            assert actual_precision <= precision, f"Expected <= {precision} decimals, got {actual_precision}"
        else:
            print(f"  Precision {precision}: {formatted} (integer format)")
    
    print("  ✓ GridInfo precision test passed")


def test_control_datum_precision():
    """Test that ControlDatum uses the correct precision."""
    print("Testing ControlDatum precision...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a scene with precision
    scene = CadScene(precision=3)
    
    # Test with different precision values
    for precision in [1, 3, 5]:
        datum = ControlDatum(
            setter=lambda x: None,
            prefix="R",
            precision=precision
        )
        
        # Test the format string
        format_string = datum.format_string
        expected_format = f"{{:.{precision}f}}"
        print(f"  Precision {precision}: format_string = '{format_string}' (expected '{expected_format}')")
        assert format_string == expected_format, f"Expected '{expected_format}', got '{format_string}'"
    
    print("  ✓ ControlDatum precision test passed")


def test_config_pane_precision():
    """Test that ConfigPane uses the correct precision."""
    print("Testing ConfigPane precision...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Test with different precision values
    for precision in [1, 3, 5]:
        config_pane = ConfigPane(precision=precision)
        
        # Create a test field
        field = {
            'name': 'test_field',
            'title': 'Test Field',
            'type': 'FLOAT',
            'min': 0.0,
            'max': 100.0,
            'increment': 0.1,
            'default': 1.234
        }
        
        # Create the field widget
        config_pane._create_float_field(0, field)
        
        # Check that the spinbox has the correct precision
        spinbox = config_pane.field_widgets['test_field']
        actual_precision = spinbox.decimals()
        print(f"  Precision {precision}: spinbox decimals = {actual_precision}")
        assert actual_precision == precision, f"Expected {precision}, got {actual_precision}"
    
    print("  ✓ ConfigPane precision test passed")


def test_scene_precision_propagation():
    """Test that scene precision is correctly propagated to CAD items."""
    print("Testing scene precision propagation...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Test with different precision values
    for precision in [1, 3, 5]:
        scene = CadScene(precision=precision)
        
        # Check that the scene returns the correct precision
        actual_precision = scene.get_precision()
        print(f"  Precision {precision}: scene.get_precision() = {actual_precision}")
        assert actual_precision == precision, f"Expected {precision}, got {actual_precision}"
        
        # Test updating precision
        new_precision = precision + 1
        scene.set_precision(new_precision)
        updated_precision = scene.get_precision()
        print(f"  Updated to {new_precision}: scene.get_precision() = {updated_precision}")
        assert updated_precision == new_precision, f"Expected {new_precision}, got {updated_precision}"
    
    print("  ✓ Scene precision propagation test passed")


def main():
    """Run all precision tests."""
    print("Running precision preference tests...")
    print()
    
    try:
        test_grid_info_precision()
        print()
        
        test_control_datum_precision()
        print()
        
        test_config_pane_precision()
        print()
        
        test_scene_precision_propagation()
        print()
        
        print("All precision preference tests passed! ✓")
        return 0
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 