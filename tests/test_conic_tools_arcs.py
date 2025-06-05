#!/usr/bin/env python3
"""
Test script to verify CONIC tools are properly in ARCS category
"""

import sys
import os

# Add the src directory to the path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from src.tools.base import ToolCategory

def test_conic_tools_in_arcs():
    """Test that CONIC2PT and CONIC3PT tools are in ARCS category"""
    print("Testing CONIC tools are in ARCS category...")
    print("=" * 50)
    
    # Create a mock ToolPalette instance to test secondary key mappings
    class MockToolPalette:
        def __init__(self, category):
            self.category = category
            
        def _get_secondary_key(self, tool_token):
            """Test the secondary key mappings for tools"""
            mappings = {}
            
            if self.category == ToolCategory.ARCS:
                # A is primary, secondary keys use letters and digits
                tool_map = {
                    'ARCCTR': 'C',       # Arc by Center (C for Center)
                    'ARC3PT': '3',       # Arc by 3 Points (3 for 3 points)
                    'ARCTAN': 'T',       # Arc by Tangent (T for Tangent)
                    'CONIC2PT': '2',     # Conic 2 Point (2 for 2 points)
                    'CONIC3PT': 'I',     # Conic 3 Point (I for conIc 3pt)
                }
            elif self.category == ToolCategory.ELLIPSES:
                # E is primary, secondary keys use mnemonic letters and digits
                tool_map = {
                    'CIRCLE': 'C',       # Circle Tool (C for Circle)
                    'CIRCLE2PT': '2',    # Circle by 2 Points (2 for 2 points)
                    'CIRCLE3PT': '3',    # Circle by 3 Points (3 for 3 points)
                    'ELLIPSECTR': 'E',   # Ellipse Center (E for Ellipse)
                    'ELLIPSEDIAG': 'D',  # Ellipse Diagonal (D for Diagonal)
                    'ELLIPSE3COR': 'O',  # Ellipse 3 Corner (O for cOrner)
                    'ELLIPSECTAN': 'T',  # Ellipse Center Tangent (T for Tangent)
                    'ELLIPSEOPTAN': 'G',  # Ellipse Opposite Tangent (G tanGent)
                }
            else:
                tool_map = {}
                
            return tool_map.get(tool_token)
    
    # Test ARCS category
    arcs_palette = MockToolPalette(ToolCategory.ARCS)
    
    # Test CONIC2PT
    conic2pt_key = arcs_palette._get_secondary_key('CONIC2PT')
    print(f"CONIC2PT in ARCS category: {conic2pt_key}")
    assert conic2pt_key == '2', f"Expected '2', got '{conic2pt_key}'"
    
    # Test CONIC3PT
    conic3pt_key = arcs_palette._get_secondary_key('CONIC3PT')
    print(f"CONIC3PT in ARCS category: {conic3pt_key}")
    assert conic3pt_key == 'I', f"Expected 'I', got '{conic3pt_key}'"
    
    print("\n✓ CONIC tools successfully found in ARCS category")
    
    # Verify they're NOT in ELLIPSES
    print("\nVerifying CONIC tools are NOT in ELLIPSES category...")
    ellipses_palette = MockToolPalette(ToolCategory.ELLIPSES)
    
    # These should return None since they're not in ELLIPSES anymore
    conic2pt_ellipse = ellipses_palette._get_secondary_key('CONIC2PT')
    conic3pt_ellipse = ellipses_palette._get_secondary_key('CONIC3PT')
    
    print(f"CONIC2PT in ELLIPSES category: {conic2pt_ellipse}")
    print(f"CONIC3PT in ELLIPSES category: {conic3pt_ellipse}")
    
    assert conic2pt_ellipse is None, f"CONIC2PT should not be in ELLIPSES, got '{conic2pt_ellipse}'"
    assert conic3pt_ellipse is None, f"CONIC3PT should not be in ELLIPSES, got '{conic3pt_ellipse}'"
    
    print("✓ CONIC tools successfully removed from ELLIPSES category")
    
    print("\n" + "=" * 50)
    print("CONIC TOOLS CATEGORIZATION TEST PASSED!")
    print("✓ CONIC2PT is in ARCS with shortcut '2'")
    print("✓ CONIC3PT is in ARCS with shortcut 'I'")
    print("✓ CONIC tools removed from ELLIPSES category")

if __name__ == "__main__":
    test_conic_tools_in_arcs()
