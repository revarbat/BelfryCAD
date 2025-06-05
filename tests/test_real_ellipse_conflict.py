#!/usr/bin/env python3

"""Test to verify the real ellipse conflict is resolved"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_real_ellipse_conflict():
    try:
        from src.gui.tool_palette import ToolPalette
        from src.tools.base import ToolCategory
        from src.tools.ellipse import (
            EllipseCenterTool,
            EllipseDiagonalTool, 
            Ellipse3CornerTool,
            EllipseCenterTangentTool,
            EllipseOppositeTangentTool
        )
        from src.tools.circle import CircleTool, Circle2PTTool, Circle3PTTool

        print("Testing Real Ellipse Tools Conflict Resolution")
        print("=" * 50)

        # Create real tool definitions
        all_ellipse_tools = [
            CircleTool,
            Circle2PTTool, 
            Circle3PTTool,
            EllipseCenterTool,
            EllipseDiagonalTool,
            Ellipse3CornerTool,
            EllipseCenterTangentTool,
            EllipseOppositeTangentTool
        ]
        
        # Get all definitions for ELLIPSES category
        ellipse_definitions = []
        for tool_class in all_ellipse_tools:
            try:
                # Create temporary instance to get definitions
                temp_tool = tool_class(None, None, None)
                for definition in temp_tool.definitions:
                    if definition.category == ToolCategory.ELLIPSES:
                        ellipse_definitions.append(definition)
                        print(f"Tool: {definition.token}, Secondary Key: '{definition.secondary_key}'")
            except Exception as e:
                print(f"Error with {tool_class.__name__}: {e}")

        # Dummy icon loader
        def dummy_icon_loader(icon_name):
            return None

        print(f"\nAttempting to create ToolPalette with {len(ellipse_definitions)} ellipse tools...")
        
        try:
            palette = ToolPalette(ToolCategory.ELLIPSES, ellipse_definitions, dummy_icon_loader)
            print("✅ SUCCESS: No duplicate key errors! Conflict resolved.")
            
            # Show the final mappings
            print("\nFinal Secondary Key Mappings:")
            for tool_def in ellipse_definitions:
                key = palette._get_secondary_key_for_tool(tool_def.token)
                print(f"  {key}: {tool_def.token} ({tool_def.name})")
                
        except ValueError as e:
            print(f"❌ CONFLICT STILL EXISTS: {e}")
            return False

        print("\n" + "=" * 50)
        print("Real conflict test completed!")
        return True

    except ImportError as e:
        print(f"Import error: {e}")
        return False

if __name__ == "__main__":
    success = True
    print("Starting real ellipse conflict test...")
    success = test_real_ellipse_conflict() and success
    
    if success:
        print("\n🎉 All tests passed! Conflicts resolved.")
    else:
        print("\n❌ Some tests failed.")
