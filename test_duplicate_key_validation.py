#!/usr/bin/env python3
"""
Test script to verify that duplicate secondary key validation works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from PySide6.QtWidgets import QApplication
from src.tools.base import ToolDefinition, ToolCategory
from src.gui.tool_palette import ToolPalette


def dummy_icon_loader(icon_name):
    """Dummy icon loader for testing"""
    return None


def test_duplicate_key_detection():
    """Test that duplicate secondary keys are detected and errors are thrown"""
    print("Testing Duplicate Secondary Key Detection")
    print("=" * 45)
    
    app = QApplication(sys.argv)
    
    # Test 1: Create tools with duplicate secondary keys in the same category
    print("\nTest 1: Creating tools with duplicate 'D' key in NODES category")
    
    conflicting_tools = [
        ToolDefinition(
            token="NODEADD",
            name="Add Node",
            category=ToolCategory.NODES,
            icon="tool-nodeadd",
            secondary_key="D"  # Duplicate key
        ),
        ToolDefinition(
            token="NODEDEL",
            name="Delete Node",
            category=ToolCategory.NODES,
            icon="tool-nodedel",
            secondary_key="D"  # Duplicate key
        ),
        ToolDefinition(
            token="NODESEL",
            name="Select Node",
            category=ToolCategory.NODES,
            icon="tool-nodesel",
            secondary_key="S"  # Unique key
        ),
    ]
    
    try:
        palette = ToolPalette(ToolCategory.NODES, conflicting_tools, dummy_icon_loader)
        print("❌ ERROR: Expected ValueError but none was thrown!")
        return False
    except ValueError as e:
        print("✅ SUCCESS: ValueError correctly thrown!")
        print(f"Error message: {e}")
    
    # Test 2: Test the existing ELLIPSES conflict
    print("\nTest 2: Testing existing ELLIPSES 'O' key conflict")
    
    ellipse_tools = [
        ToolDefinition(
            token="ELLIPSEOPTAN",
            name="Ellipse Opposite Tangent",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipseoptan",
            secondary_key="O"  # This will trigger special case
        ),
        ToolDefinition(
            token="ELLIPSE3CRN",
            name="Ellipse 3 Corner",
            category=ToolCategory.ELLIPSES,
            icon="tool-ellipse3crn",
            secondary_key="O"  # This will trigger special case
        ),
    ]
    
    try:
        palette = ToolPalette(ToolCategory.ELLIPSES, ellipse_tools, dummy_icon_loader)
        print("❌ ERROR: Expected ValueError but none was thrown!")
        return False
    except ValueError as e:
        print("✅ SUCCESS: ValueError correctly thrown for ELLIPSES conflict!")
        print(f"Error message: {e}")
    
    # Test 3: Create tools with no conflicts (should work fine)
    print("\nTest 3: Creating tools with unique secondary keys")
    
    valid_tools = [
        ToolDefinition(
            token="NODEADD",
            name="Add Node",
            category=ToolCategory.NODES,
            icon="tool-nodeadd",
            secondary_key="A"  # Unique key
        ),
        ToolDefinition(
            token="NODEDEL",
            name="Delete Node",
            category=ToolCategory.NODES,
            icon="tool-nodedel",
            secondary_key="D"  # Unique key
        ),
        ToolDefinition(
            token="NODESEL",
            name="Select Node",
            category=ToolCategory.NODES,
            icon="tool-nodesel",
            secondary_key="S"  # Unique key
        ),
    ]
    
    try:
        palette = ToolPalette(ToolCategory.NODES, valid_tools, dummy_icon_loader)
        print("✅ SUCCESS: No error thrown for unique keys!")
        print(f"Mappings: {palette.secondary_key_mappings}")
    except ValueError as e:
        print(f"❌ ERROR: Unexpected ValueError: {e}")
        return False
    
    print("\n" + "=" * 45)
    print("All tests completed successfully!")
    return True


if __name__ == "__main__":
    success = test_duplicate_key_detection()
    sys.exit(0 if success else 1)
