#!/usr/bin/env python3
"""
Test script to verify that the new ellipse tools are properly integrated.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ellipse_tools():
    """Test that all ellipse tools can be imported and instantiated."""
    print("Testing ellipse tools...")

    try:
        from BelfryCAD.tools.ellipse import (
            EllipseCenterTool,
            EllipseDiagonalTool,
            Ellipse3CornerTool,
            EllipseCenterTangentTool,
            EllipseOppositeTangentTool
        )
        print("✓ All ellipse tools imported successfully")

        # Test tool definitions
        tools = [
            EllipseCenterTool,
            EllipseDiagonalTool,
            Ellipse3CornerTool,
            EllipseCenterTangentTool,
            EllipseOppositeTangentTool
        ]

        for tool_class in tools:
            # Create a temporary instance to test the definition
            try:
                # We can't fully instantiate without a document,
                # but we can test the class exists and has the right methods
                assert hasattr(tool_class, '_get_definition')
                assert hasattr(tool_class, 'handle_mouse_down')
                assert hasattr(tool_class, 'handle_mouse_move')
                assert hasattr(tool_class, 'create_object')
                print(f"✓ {tool_class.__name__} has required methods")
            except Exception as e:
                print(f"✗ {tool_class.__name__} failed validation: {e}")
                return False

        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_tool_registration():
    """Test that the tools are properly registered in the available_tools list."""
    print("\nTesting tool registration...")

    try:
        from BelfryCAD.tools import available_tools

        # Get tool class names
        tool_names = [tool.__name__ for tool in available_tools]

        required_tools = [
            'Ellipse3CornerTool',
            'EllipseCenterTangentTool',
            'EllipseOppositeTangentTool'
        ]

        for tool_name in required_tools:
            if tool_name in tool_names:
                print(f"✓ {tool_name} is registered")
            else:
                print(f"✗ {tool_name} is NOT registered")
                return False

        return True

    except Exception as e:
        print(f"✗ Registration test failed: {e}")
        return False

def test_icon_files():
    """Test that all required icon files exist."""
    print("\nTesting icon files...")

    required_icons = [
        'images/tool-ellipse3crn.png',
        'images/tool-ellipsectrtan.png',
        'images/tool-ellipseopptan.png'
    ]

    for icon_path in required_icons:
        if os.path.exists(icon_path):
            print(f"✓ {icon_path} exists")
        else:
            print(f"✗ {icon_path} missing")
            return False

    return True

def main():
    """Run all tests."""
    print("=== PyTkCAD New Ellipse Tools Test ===\n")

    tests = [
        test_ellipse_tools,
        test_tool_registration,
        test_icon_files
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()

    if all_passed:
        print("🎉 All tests passed! The new ellipse tools are ready to use.")
    else:
        print("❌ Some tests failed. Please check the implementation.")

    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
