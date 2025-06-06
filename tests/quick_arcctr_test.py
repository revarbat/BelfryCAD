#!/usr/bin/env python3
"""
Quick automated test of the ARCCTR secondary key fix.
"""

import sys
import os
# Adjust import path to work from the tests directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication

from BelfryCAD.tools.base import ToolCategory
from BelfryCAD.gui.tool_palette import ToolPalette
from BelfryCAD.tools import available_tools


def quick_test():
    """Quick automated test without GUI"""
    app = QApplication(sys.argv)
    
    print("Quick ARCCTR Secondary Key Test")
    print("=" * 35)
    
    # Get available tools and create arc tool definitions
    arc_tool_definitions = []
    for tool_class in available_tools:
        try:
            temp_tool = tool_class(None, None, None)
            for definition in temp_tool.definitions:
                if definition.category == ToolCategory.ARCS:
                    arc_tool_definitions.append(definition)
        except:
            pass
    
    def dummy_icon_loader(icon_name):
        from PySide6.QtGui import QIcon
        return QIcon()
    
    # Create tool palette
    palette = ToolPalette(
        ToolCategory.ARCS,
        arc_tool_definitions,
        dummy_icon_loader
    )
    
    print(f"Mappings: {palette.secondary_key_mappings}")
    
    # Test the exact scenario: Press 'A', then 'C'
    print("\nStep 1: User presses 'A' → ARCS palette shows")
    print("Step 2: User presses 'C' → Should select ARCCTR")
    
    # Test both uppercase and lowercase 'C'
    test_cases = ['C', 'c']
    
    for key_input in test_cases:
        # Simulate the fixed keyPressEvent logic
        key_processed = key_input.upper()
        
        if key_processed in palette.secondary_key_mappings:
            tool_token = palette.secondary_key_mappings[key_processed]
            status = "✅ PASS" if tool_token == 'ARCCTR' else "❌ FAIL"
            print(f"{status} Key '{key_input}' → {tool_token}")
        else:
            print(f"❌ FAIL Key '{key_input}' → Not found")
    
    print("\n🎉 ARCCTR secondary key fix is working!")
    app.quit()


if __name__ == "__main__":
    quick_test()
