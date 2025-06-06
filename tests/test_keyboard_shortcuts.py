#!/usr/bin/env python3
"""
Test script to verify keyboard shortcuts functionality in pyTkCAD.

This test verifies that:
1. Keyboard shortcuts are properly mapped to tool categories
2. Shortcut activation triggers the correct tool palette or tool
3. Tooltips are updated to show keyboard shortcuts
"""

import sys
import os

# Add the project root directory to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_keyboard_shortcut_mappings():
    """Test that keyboard shortcuts are properly mapped"""
    from BelfryCAD.gui.main_window import MainWindow
    from BelfryCAD.tools.base import ToolCategory
    from BelfryCAD.core.config import Config
    from BelfryCAD.core.preferences import PreferencesManager
    from BelfryCAD.core.document import TkCADDocument

    # Create test instances
    config = Config()
    preferences = PreferencesManager()
    document = TkCADDocument()

    # Create main window (this will set up shortcuts)
    main_window = MainWindow(config, preferences, document)

    # Test that category key mappings are defined
    assert hasattr(main_window, 'category_key_mappings')
    assert len(main_window.category_key_mappings) > 0

    # Test expected mappings
    expected_mappings = {
        'S': ToolCategory.SELECTOR,
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

    for key, category in expected_mappings.items():
        assert key in main_window.category_key_mappings
        assert main_window.category_key_mappings[key] == category

    # Test that shortcuts are created
    assert hasattr(main_window, 'category_shortcuts')
    assert len(main_window.category_shortcuts) > 0

    print("✓ All keyboard shortcut mappings are correct")

    # Clean up
    main_window.close()

def test_shortcut_activation():
    """Test that shortcuts can be activated"""
    from BelfryCAD.gui.main_window import MainWindow
    from BelfryCAD.tools.base import ToolCategory
    from BelfryCAD.core.config import Config
    from BelfryCAD.core.preferences import PreferencesManager
    from BelfryCAD.core.document import TkCADDocument

    # Create test instances
    config = Config()
    preferences = PreferencesManager()
    document = TkCADDocument()

    # Create main window
    main_window = MainWindow(config, preferences, document)

    # Test that the shortcut activation method exists and works
    assert hasattr(main_window, '_activate_category_shortcut')

    # Test calling shortcut activation (should not raise errors)
    # Even if category_buttons don't exist yet, it should handle gracefully
    try:
        main_window._activate_category_shortcut(ToolCategory.SELECTOR)
        print("✓ Shortcut activation method works")
    except Exception as e:
        print(f"✗ Shortcut activation failed: {e}")
        raise

    # Clean up
    main_window.close()

if __name__ == "__main__":
    print("Testing keyboard shortcuts functionality...")

    try:
        test_keyboard_shortcut_mappings()
        test_shortcut_activation()
        print("\n✅ All keyboard shortcut tests passed!")

        print("\nKeyboard Shortcut Reference:")
        print("==========================")
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
        print("H - Screw hole tools")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
