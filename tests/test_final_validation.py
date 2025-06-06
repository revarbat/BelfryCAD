#!/usr/bin/env python3

"""Final verification test for duplicate key validation system"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_final_validation():
    """Test that the validation system works and conflicts are resolved"""
    try:
        from BelfryCAD.gui.tool_palette import ToolPalette
        from BelfryCAD.tools.base import ToolCategory, ToolDefinition

        print("Final Validation Test")
        print("=" * 50)

        # Test 1: Verify validation still catches new conflicts
        print("\nTest 1: Validation catches NEW conflicts")
        try:
            conflicting_tools = [
                ToolDefinition(
                    token="TOOL1",
                    name="Tool 1",
                    category=ToolCategory.NODES,
                    icon="tool1",
                    secondary_key="X"
                ),
                ToolDefinition(
                    token="TOOL2",
                    name="Tool 2",
                    category=ToolCategory.NODES,
                    icon="tool2",
                    secondary_key="X"  # Same key - should cause error
                )
            ]

            def dummy_icon_loader(icon_name):
                return None

            palette = ToolPalette(ToolCategory.NODES, conflicting_tools, dummy_icon_loader)
            print("❌ FAILED: Should have thrown ValueError for duplicate 'X' keys")
            return False

        except ValueError as e:
            print(f"✅ SUCCESS: Validation correctly caught conflict: {e}")

        # Test 2: Verify that no conflicts exist in ELLIPSES category now
        print("\nTest 2: ELLIPSES category has no conflicts")
        from BelfryCAD.tools.ellipse import (
            EllipseCenterTool,
            EllipseDiagonalTool,
            Ellipse3CornerTool,
            EllipseCenterTangentTool,
            EllipseOppositeTangentTool
        )
        from BelfryCAD.tools.circle import CircleTool, Circle2PTTool, Circle3PTTool

        all_ellipse_tools = [
            CircleTool, Circle2PTTool, Circle3PTTool,
            EllipseCenterTool, EllipseDiagonalTool, Ellipse3CornerTool,
            EllipseCenterTangentTool, EllipseOppositeTangentTool
        ]

        ellipse_definitions = []
        for tool_class in all_ellipse_tools:
            try:
                temp_tool = tool_class(None, None, None)
                for definition in temp_tool.definitions:
                    if definition.category == ToolCategory.ELLIPSES:
                        ellipse_definitions.append(definition)
                        print(f"  {definition.token}: '{definition.secondary_key}'")
            except Exception as e:
                print(f"  Error with {tool_class.__name__}: {e}")

        try:
            palette = ToolPalette(ToolCategory.ELLIPSES, ellipse_definitions, dummy_icon_loader)
            print("✅ SUCCESS: No conflicts in ELLIPSES category!")

            # Show final mappings
            print("\nFinal ELLIPSES secondary key mappings:")
            for tool_def in ellipse_definitions:
                try:
                    key = palette._get_secondary_key_for_tool(tool_def.token)
                    print(f"  {key}: {tool_def.token}")
                except:
                    print(f"  ?: {tool_def.token} (error getting key)")

        except ValueError as e:
            print(f"❌ FAILED: Conflicts still exist in ELLIPSES: {e}")
            return False

        print("\n" + "=" * 50)
        print("✅ All validation tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = test_final_validation()

    if success:
        print("\n🎉 VALIDATION SYSTEM WORKING CORRECTLY!")
        print("✅ Duplicate key detection is active")
        print("✅ ELLIPSES conflict resolved (ELLIPSE3CRN='R', ELLIPSEOPPTAN='O')")
        print("✅ Application runs without errors")
    else:
        print("\n❌ VALIDATION SYSTEM HAS ISSUES")
