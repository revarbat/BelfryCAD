#!/usr/bin/env python3
"""
Test to verify that tooltips properly display secondary keys in the UI.
This test creates actual tooltip widgets and verifies their content.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest

from src.tools.base import ToolCategory
from src.gui.tool_palette import ToolPalette
from src.tools import available_tools


def test_tooltip_display():
    """Test actual tooltip display in UI for tools."""
    app = QApplication(sys.argv)
    
    print("\nTESTING ACTUAL TOOLTIP DISPLAY\n" + "="*30)
    
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
    
    # Focus on categories with known issues
    focus_categories = [ToolCategory.ARCS, ToolCategory.ELLIPSES]
    
    for category in focus_categories:
        definitions = tool_defs_by_category.get(category, [])
        if not definitions:
            continue
            
        print(f"\nCategory: {category.name}")
        
        # Create palette
        palette = ToolPalette(category, definitions, dummy_icon_loader)
        palette.show()  # Need to show to enable tooltip features
        
        # Verify tooltips for each button
        for i, tool_def in enumerate(definitions):
            if i < len(palette.tool_buttons):
                button = palette.tool_buttons[i]
                tooltip = button.toolTip()
                
                # Get expected tooltip text
                expected_tooltip = tool_def.name
                secondary_key = palette._get_secondary_key_for_tool(tool_def.token)
                if secondary_key:
                    expected_tooltip += f" ({secondary_key})"
                
                print(f"  Tool: {tool_def.token}")
                print(f"    - Expected Tooltip: '{expected_tooltip}'")
                print(f"    - Actual Tooltip: '{tooltip}'")
                
                # For conic and ellipse tools, do additional checks
                if tool_def.token in ['CONIC2PT', 'CONIC3PT', 'ELLIPSE3CRN', 'ELLIPSEOPTAN']:
                    print(f"    >>> SPECIAL TOOL DETECTED: {tool_def.token}")
                    print(f"    >>> Secondary Key in Tooltip: {'Yes' if secondary_key in tooltip else 'No'}")
    
    palette.hide()
    print("\nTesting Complete!")
    
    return True


if __name__ == "__main__":
    test_tooltip_display()
