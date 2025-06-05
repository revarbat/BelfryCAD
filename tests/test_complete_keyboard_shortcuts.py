#!/usr/bin/env python3
"""
Comprehensive Test Script for Keyboard Shortcuts in pyTkCAD

This test verifies the complete two-keystroke shortcut system:
1. Primary shortcuts (Space, N, L, A, E, P, T, I, D, F, Y, U, O, H)
2. Secondary shortcuts (letters) for tool selection within palettes

Usage:
    python test_complete_keyboard_shortcuts.py
"""

import os
import sys

# Add the project root directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication

from src.config import AppConfig
from src.core.document import Document
from src.core.preferences import PreferencesManager
from src.gui.main_window import MainWindow
from src.tools.base import ToolCategory


def test_primary_shortcuts():
    """Test primary keyboard shortcuts functionality"""
    print("Testing Primary Keyboard Shortcuts")
    print("==================================")

    # Create test instances
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()

    # Create main window
    main_window = MainWindow(config, preferences, document)

    # Test that shortcut mappings exist
    assert hasattr(main_window, 'category_key_mappings'), \
        "category_key_mappings not found"
    assert hasattr(main_window, 'category_shortcuts'), \
        "category_shortcuts not found"

    expected_mappings = {
        'Space': ToolCategory.SELECTOR,
        'N': ToolCategory.NODES,
        'L': ToolCategory.LINES,
        'A': ToolCategory.ARCS,
        'E': ToolCategory.ELLIPSES,
        'P': ToolCategory.POLYGONS,
        'T': ToolCategory.TEXT,
        'I': ToolCategory.IMAGES,
        'D': ToolCategory.DIMENSIONS,
        'F': ToolCategory.TRANSFORMS,
        'Y': ToolCategory.LAYOUT,
        'U': ToolCategory.DUPLICATORS,
        'O': ToolCategory.POINTS,
        'H': ToolCategory.SCREWHOLES,
    }

    # Verify all expected mappings exist
    for key, category in expected_mappings.items():
        assert key in main_window.category_key_mappings, \
            f"Key '{key}' not found in mappings"
        assert main_window.category_key_mappings[key] == category, \
            f"Key '{key}' maps to wrong category"
        assert category in main_window.category_shortcuts, \
            f"Shortcut for {category} not created"

    print("✓ All primary keyboard shortcut mappings are correct")

    # Test shortcut activation method
    assert hasattr(main_window, '_activate_category_shortcut'), \
        "_activate_category_shortcut method not found"

    # Test that shortcut activation doesn't crash
    # (even without UI fully initialized)
    try:
        main_window._activate_category_shortcut(ToolCategory.NODES)
        print("✓ Primary shortcut activation method works")
    except Exception as e:
        print(f"✗ Primary shortcut activation failed: {e}")
        raise

    main_window.close()
    print("✓ Primary keyboard shortcuts test completed\n")


def test_secondary_shortcuts():
    """Test secondary keyboard shortcuts in tool palettes"""
    print("Testing Secondary Keyboard Shortcuts")
    print("===================================")

    from src.gui.tool_palette import ToolPalette
    from src.tools.base import ToolDefinition

    # Test secondary key mappings for different categories
    test_cases = [
        {
            'category': ToolCategory.NODES,
            'tools': [
                ToolDefinition(
                    token='NODESEL',
                    name='Select Nodes',
                    category=ToolCategory.NODES,
                    icon='tool-nodesel'
                ),
                ToolDefinition(
                    token='NODEADD',
                    name='Add Node',
                    category=ToolCategory.NODES,
                    icon='tool-nodeadd'
                ),
                ToolDefinition(
                    token='NODEDEL',
                    name='Delete Node',
                    category=ToolCategory.NODES,
                    icon='tool-nodedel'
                ),
                ToolDefinition(
                    token='REORIENT',
                    name='Reorient',
                    category=ToolCategory.NODES,
                    icon='tool-reorient'
                ),
                ToolDefinition(
                    token='CONNECT',
                    name='Connect',
                    category=ToolCategory.NODES,
                    icon='tool-connect'
                ),
            ],
            'expected_mappings': {
                'S': 'NODESEL',
                'A': 'NODEADD',
                'D': 'NODEDEL',
                'R': 'REORIENT',
                'C': 'CONNECT',
            }
        },
        {
            'category': ToolCategory.ELLIPSES,
            'tools': [
                ToolDefinition(
                    token='CIRCLE',
                    name='Circle Tool',
                    category=ToolCategory.ELLIPSES,
                    icon='tool-circlectr'
                ),
                ToolDefinition(
                    token='CIRCLE2PT',
                    name='Circle by 2 Points',
                    category=ToolCategory.ELLIPSES,
                    icon='tool-circle2pt'
                ),
                ToolDefinition(
                    token='CIRCLE3PT',
                    name='Circle by 3 Points',
                    category=ToolCategory.ELLIPSES,
                    icon='tool-circle3pt'
                ),
                ToolDefinition(
                    token='ELLIPSECTR',
                    name='Ellipse Center',
                    category=ToolCategory.ELLIPSES,
                    icon='tool-ellipsectr'
                ),
                ToolDefinition(
                    token='CONIC2PT',
                    name='Conic 2 Point',
                    category=ToolCategory.ELLIPSES,
                    icon='tool-conic2pt'
                ),
                ToolDefinition(
                    token='CONIC3PT',
                    name='Conic 3 Point',
                    category=ToolCategory.ELLIPSES,
                    icon='tool-conic3pt'
                ),
            ],
            'expected_mappings': {
                'C': 'CIRCLE',
                'T': 'CIRCLE2PT',
                'H': 'CIRCLE3PT',
                'N': 'ELLIPSECTR',
                'O': 'CONIC2PT',
                'I': 'CONIC3PT',
            }
        }
    ]

    def dummy_icon_loader(icon_name):
        return None  # Return None for testing

    for test_case in test_cases:
        category = test_case['category']
        tools = test_case['tools']
        expected_mappings = test_case['expected_mappings']

        # Create tool palette
        palette = ToolPalette(category, tools, dummy_icon_loader)

        # Verify secondary key mappings
        for key, expected_token in expected_mappings.items():
            assert key in palette.secondary_key_mappings, \
                f"Key '{key}' not found in {category} secondary mappings"
            actual_token = palette.secondary_key_mappings[key]
            assert actual_token == expected_token, \
                f"Key '{key}' maps to '{actual_token}', expected " \
                f"'{expected_token}'"

        # Test reverse lookup
        for tool_def in tools:
            if tool_def.token in expected_mappings.values():
                secondary_key = palette._get_secondary_key_for_tool(
                    tool_def.token)
                assert secondary_key != "", \
                    f"No secondary key found for tool {tool_def.token}"
                assert secondary_key in expected_mappings, \
                    f"Unexpected secondary key '{secondary_key}' " \
                    f"for tool {tool_def.token}"

        print(f"✓ Secondary shortcuts for {category.value} category "
              "are correct")

    print("✓ Secondary keyboard shortcuts test completed\n")


def test_integration():
    """Test that primary and secondary shortcuts work together"""
    print("Testing Primary + Secondary Integration")
    print("=====================================")

    # Create test instances
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()

    # Create main window
    main_window = MainWindow(config, preferences, document)

    # Show window (required for proper initialization)
    main_window.show()

    # Process events to ensure UI is initialized
    QApplication.processEvents()

    # Test that category buttons exist and have tool palettes
    if hasattr(main_window, 'category_buttons'):
        for category, button in main_window.category_buttons.items():
            assert hasattr(button, 'tools'), \
                f"Category button for {category} has no tools"
            assert len(button.tools) > 0, \
                f"Category button for {category} has empty tools list"

            # For multi-tool categories, verify palette creation
            if len(button.tools) > 1:
                # Trigger palette creation (simulates keyboard shortcut)
                button._show_palette()
                assert button.palette is not None, \
                    f"Palette not created for {category}"
                assert hasattr(button.palette, 'secondary_key_mappings'), \
                    f"Palette for {category} has no secondary mappings"

                # Hide palette
                button.palette.hide()

        print("✓ Category buttons and palettes properly integrated")
    else:
        print("⚠ Category buttons not yet initialized "
              "(UI not fully loaded)")

    main_window.close()
    print("✓ Integration test completed\n")


def print_keyboard_reference():
    """Print a comprehensive keyboard shortcut reference"""
    print("Complete Keyboard Shortcut Reference")
    print("===================================")
    print()
    print("PRIMARY SHORTCUTS (Tool Categories):")
    print("------------------------------------")
    print("Space - Selector tools")
    print("N - Node tools")
    print("L - Line tools")
    print("A - Arc tools")
    print("E - Ellipse tools")
    print("P - Polygon tools")
    print("T - Text tools")
    print("I - Image tools")
    print("D - Dimension tools")
    print("F - Transform tools")
    print("Y - Layout tools")
    print("U - Duplicator tools")
    print("O - Point tools")
    print("H - Screw Hole tools")
    print()
    print("SECONDARY SHORTCUTS (After primary shortcut shows palette):")
    print("-----------------------------------------------------------")
    print("Node Tools (N + secondary key):")
    print("  S - Select Nodes")
    print("  A - Add Node")
    print("  D - Delete Node")
    print("  R - Reorient")
    print("  C - Connect")
    print()
    print("Line Tools (L + secondary key):")
    print("  L - Line")
    print("  M - Multi-Point Line")
    print("  P - Polyline")
    print("  B - Bezier")
    print("  Q - Bezier Quad")
    print()
    print("Arc Tools (A + secondary key):")
    print("  C - Arc by Center")
    print("  3 - Arc by 3 Points")
    print("  T - Arc by Tangent")
    print()
    print("Ellipse Tools (E + secondary key):")
    print("  C - Circle")
    print("  T - Circle by 2 Points")
    print("  H - Circle by 3 Points")
    print("  N - Ellipse Center")
    print("  D - Ellipse Diagonal")
    print("  R - Ellipse 3 Corner")
    print("  A - Ellipse Center Tangent")
    print("  G - Ellipse Opposite Tangent")
    print("  O - Conic 2 Point")
    print("  I - Conic 3 Point")
    print()
    print("Polygon Tools (P + secondary key):")
    print("  R - Rectangle")
    print("  G - Regular Polygon")
    print()
    print("Dimension Tools (D + secondary key):")
    print("  H - Horizontal Dimension")
    print("  V - Vertical Dimension")
    print("  L - Linear Dimension")
    print("  A - Arc Dimension")
    print()
    print("Transform Tools (F + secondary key):")
    print("  T - Translate")
    print("  R - Rotate")
    print("  S - Scale")
    print("  F - Flip")
    print("  H - Shear")
    print("  B - Bend")
    print("  W - Wrap")
    print("  U - Un-wrap")
    print()
    print("Duplicator Tools (U + secondary key):")
    print("  L - Linear Copy")
    print("  R - Radial Copy")
    print("  G - Grid Copy")
    print("  O - Offset Copy")
    print()
    print("USAGE:")
    print("------")
    print("1. For single-tool categories: Press primary key (e.g., 'Space') "
          "to activate tool directly")
    print("2. For multi-tool categories: Press primary key (e.g., 'N') to "
          "show palette, then secondary key (e.g., 'A') to select tool")
    print("3. Tooltips show available secondary shortcuts when palette is "
          "visible")
    print("4. Press Escape to close an open palette")


if __name__ == "__main__":
    print("Comprehensive Keyboard Shortcuts Test for pyTkCAD")
    print("================================================")
    print()

    # Create QApplication for testing
    app = QApplication([])

    try:
        test_primary_shortcuts()
        test_secondary_shortcuts()
        test_integration()

        print("🎉 ALL KEYBOARD SHORTCUT TESTS PASSED!")
        print()
        print_keyboard_reference()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    finally:
        app.quit()
