#!/usr/bin/env python3
"""
Test to verify that secondary keys are properly displayed in tooltips
for conic tools and other tools.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from BelfryCAD.tools.base import ToolCategory
from BelfryCAD.gui.tool_palette import ToolPalette
from BelfryCAD.tools import available_tools


def test_tool_tooltips():
    """Test tooltips for all tools to verify secondary keys are displayed."""
    app = QApplication(sys.argv)
    
    print("\nTESTING TOOLTIPS FOR TOOLS\n" + "="*30)
    
    # Create tool definitions for each category
    tool_defs_by_category = {}
    
    for tool_class in available_tools:
        try:
            temp_tool = tool_class(None, None, None)
            for definition in temp_tool.definitions:
                category = definition.category
                if category not in tool_defs_by_category:
                    tool_defs_by_category[category] = []
                tool_defs_by_category[category].append(definition)
        except Exception as e:
            print(f"Error creating tool {tool_class.__name__}: {e}")
    
    # Dummy icon loader
    def dummy_icon_loader(icon_name):
        from PySide6.QtGui import QIcon
        return QIcon()
    
    # Test each category
    for category, definitions in tool_defs_by_category.items():
        print(f"\nCategory: {category.name}")
        
        # Create palette
        palette = ToolPalette(category, definitions, dummy_icon_loader)
        
        # Check secondary keys and tooltips
        for tool_def in definitions:
            secondary_key = palette._get_secondary_key_for_tool(tool_def.token)
            print(f"  Tool: {tool_def.token}")
            print(f"    - Name: {tool_def.name}")
            print(f"    - Secondary Key (defined): {tool_def.secondary_key}")
            print(f"    - Secondary Key (from palette): {secondary_key}")
            
            # For conic tools, do additional checks
            if tool_def.token in ['CONIC2PT', 'CONIC3PT']:
                print(f"    >>> CONIC TOOL DETECTED: {tool_def.token}")
                print(f"    >>> Secondary Key: '{tool_def.secondary_key}'")
    
    print("\nTesting Complete!")
    
    return True


if __name__ == "__main__":
    test_tool_tooltips()
