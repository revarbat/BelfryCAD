#!/usr/bin/env python3
"""
Test script to verify ControlDatum tooltips work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from BelfryCAD.gui.views.graphics_items.control_points import ControlDatum


def test_control_datum_tooltips():
    """Test that ControlDatum tooltips work correctly."""
    print("Testing ControlDatum tooltips...")
    
    # Test 1: Explicit label
    datum1 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        label="Pitch Diameter",
        precision=3
    )
    tooltip1 = datum1._get_tooltip_text()
    print(f"  Explicit label 'Pitch Diameter': {tooltip1}")
    assert tooltip1 == "Pitch Diameter", f"Expected 'Pitch Diameter', got '{tooltip1}'"
    
    # Test 2: Prefix-based label (Radius)
    datum2 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        prefix="R",
        precision=3
    )
    tooltip2 = datum2._get_tooltip_text()
    print(f"  Prefix 'R': {tooltip2}")
    assert tooltip2 == "Radius", f"Expected 'Radius', got '{tooltip2}'"
    
    # Test 3: Prefix-based label (Diameter)
    datum3 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        prefix="D",
        precision=3
    )
    tooltip3 = datum3._get_tooltip_text()
    print(f"  Prefix 'D': {tooltip3}")
    assert tooltip3 == "Diameter", f"Expected 'Diameter', got '{tooltip3}'"
    
    # Test 4: Prefix-based label (Pressure Angle)
    datum4 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        prefix="PA: ",
        precision=3
    )
    tooltip4 = datum4._get_tooltip_text()
    print(f"  Prefix 'PA: ': {tooltip4}")
    assert tooltip4 == "Pressure Angle", f"Expected 'Pressure Angle', got '{tooltip4}'"
    
    # Test 5: Prefix-based label (Tooth Count)
    datum5 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        prefix="T: ",
        precision=3
    )
    tooltip5 = datum5._get_tooltip_text()
    print(f"  Prefix 'T: ': {tooltip5}")
    assert tooltip5 == "Tooth Count", f"Expected 'Tooth Count', got '{tooltip5}'"
    
    # Test 6: Prefix-based label (Module)
    datum6 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        prefix="m: ",
        precision=3
    )
    tooltip6 = datum6._get_tooltip_text()
    print(f"  Prefix 'm: ': {tooltip6}")
    assert tooltip6 == "Module", f"Expected 'Module', got '{tooltip6}'"
    
    # Test 7: Prefix-based label (Diametral Pitch)
    datum7 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        prefix="DP: ",
        precision=3
    )
    tooltip7 = datum7._get_tooltip_text()
    print(f"  Prefix 'DP: ': {tooltip7}")
    assert tooltip7 == "Diametral Pitch", f"Expected 'Diametral Pitch', got '{tooltip7}'"
    
    # Test 8: Generic prefix
    datum8 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        prefix="Custom: ",
        precision=3
    )
    tooltip8 = datum8._get_tooltip_text()
    print(f"  Prefix 'Custom: ': {tooltip8}")
    assert tooltip8 == "Custom", f"Expected 'Custom', got '{tooltip8}'"
    
    # Test 9: No label or prefix (fallback)
    datum9 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        precision=3
    )
    tooltip9 = datum9._get_tooltip_text()
    print(f"  No label/prefix: {tooltip9}")
    assert tooltip9 == "Value", f"Expected 'Value', got '{tooltip9}'"
    
    # Test 10: Default label "value" should use prefix instead
    datum10 = ControlDatum(
        setter=lambda x: None,
        cad_item=None,
        label="value",  # Default label
        prefix="R",
        precision=3
    )
    tooltip10 = datum10._get_tooltip_text()
    print(f"  Default label with prefix 'R': {tooltip10}")
    assert tooltip10 == "Radius", f"Expected 'Radius', got '{tooltip10}'"
    
    print("  ✓ All ControlDatum tooltip tests passed!")


def main():
    """Run all ControlDatum tooltip tests."""
    print("Running ControlDatum tooltip tests...")
    
    try:
        test_control_datum_tooltips()
        print("\nAll ControlDatum tooltip tests passed! ✓")
        return True
    except Exception as e:
        print(f"\nTest failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 